"""
scripts/seed_precedents.py
--------------------------
Precedent Corpus Seeder.

What this file does:
  Reads court case summary files from services/ai/data/precedents/ (organised
  into subdirectories: employment, ip, nda, vendor), embeds each summary with
  sentence-transformers (all-MiniLM-L6-v2), and inserts the resulting vectors
  into the `embeddings` table in PostgreSQL (pgvector extension required).

  Each row stored:
    - embedding_type  = "precedent"
    - content         = full text of the case summary
    - embedding       = 384-dim float vector
    - metadata (JSONB) = {
          "case_name":    str,
          "jurisdiction": str,
          "year":         int,
          "outcome":      str,
          "clause_type":  str   (subdirectory name: employment|ip|nda|vendor)
      }

  Usage:
      python scripts/seed_precedents.py [--dsn postgresql://...]
                                        [--data-dir services/ai/data/precedents]
                                        [--reset]

  Flags:
      --dsn       Postgres DSN (falls back to env var DATABASE_URL).
      --data-dir  Root of the precedents directory tree.
      --reset     DELETE existing precedent rows before seeding (idempotent re-run).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_TYPE = "precedent"

# Maps subdirectory name → clause_type stored in metadata
DOMAIN_TO_CLAUSE_TYPE: dict[str, str] = {
    "employment": "non_compete",
    "ip": "ip_assignment",
    "nda": "nda",
    "vendor": "vendor",
}

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _extract_field(text: str, field: str) -> str:
    """Extract a value from a line like 'FIELD: value'."""
    pattern = re.compile(rf"^{field}:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def parse_case_file(path: Path, clause_type: str) -> dict:
    """
    Parse a .txt precedent file and return a structured dict ready for DB
    insertion.  Expected file format (all fields optional except CASE):

        CASE: <Name>, <year>
        JURISDICTION: <...>
        OUTCOME: <...>
        CLAUSE_TYPE: <...>

        SUMMARY:
        <free-form text>
    """
    raw = path.read_text(encoding="utf-8")

    case_line = _extract_field(raw, "CASE")
    # Try to extract year from the CASE line: "BioSyn Corp. v. Hartwell, 2019"
    year_match = re.search(r"\b(19|20)\d{2}\b", case_line)
    year = int(year_match.group(0)) if year_match else 0
    case_name = re.sub(r",?\s*\d{4}\s*$", "", case_line).strip()

    jurisdiction = _extract_field(raw, "JURISDICTION")
    outcome = _extract_field(raw, "OUTCOME")

    # Grab everything after "SUMMARY:" as the content
    summary_match = re.search(r"SUMMARY:\s*\n(.*)", raw, re.DOTALL | re.IGNORECASE)
    content = summary_match.group(1).strip() if summary_match else raw.strip()

    return {
        "case_name": case_name or path.stem,
        "jurisdiction": jurisdiction,
        "year": year,
        "outcome": outcome,
        "clause_type": clause_type,
        "text": content,
    }


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def ensure_embeddings_table(conn) -> None:
    """Verify the embeddings table exists (schema is managed by migrations)."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'embeddings'
            );
            """
        )
        table_exists = cur.fetchone()[0]
        if not table_exists:
            raise RuntimeError(
                "embeddings table does not exist. Run migrations first."
            )
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'embeddings_vector_idx'
                AND n.nspname = 'public'
            );
            """
        )
        index_exists = cur.fetchone()[0]
        if not index_exists:
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS embeddings_vector_idx
                ON embeddings
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
                """
            )
            conn.commit()
    logger.info("embeddings table and index verified.")


def reset_precedents(conn) -> int:
    """Delete all existing precedent rows and return the count removed."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM embeddings WHERE embedding_type = %s RETURNING id;",
            (EMBEDDING_TYPE,),
        )
        deleted = cur.rowcount
        conn.commit()
    logger.info("Deleted %d existing precedent rows.", deleted)
    return deleted


def insert_precedent(conn, record: dict, vector: list[float]) -> int:
    """Insert one precedent row and return its new id."""
    import uuid
    vector_str = "[" + ",".join(f"{x:.8f}" for x in vector) + "]"
    row_id = str(uuid.uuid4())
    sql = """
        INSERT INTO embeddings
            (id, embedding_type, text, embedding, metadata)
        VALUES (%s, %s, %s, %s::vector, %s)
        RETURNING id;
    """
    metadata = {
        "case_name":    record["case_name"],
        "jurisdiction": record["jurisdiction"],
        "year":         record["year"],
        "outcome":      record["outcome"],
        "clause_type":  record["clause_type"],
    }
    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                row_id,
                EMBEDDING_TYPE,
                record["text"],
                vector_str,
                json.dumps(metadata),
            ),
        )
        inserted_id = cur.fetchone()[0]
        conn.commit()
    return inserted_id


# ---------------------------------------------------------------------------
# Main seeding logic
# ---------------------------------------------------------------------------


def seed(data_dir: Path, dsn: str, reset: bool = False) -> int:
    """
    Seed the precedent corpus.

    Returns the total number of rows inserted.
    """
    logger.info("Connecting to database…")
    conn = psycopg2.connect(dsn)
    ensure_embeddings_table(conn)

    if reset:
        reset_precedents(conn)

    logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)

    inserted = 0
    skipped = 0

    for domain_dir in sorted(data_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        clause_type = DOMAIN_TO_CLAUSE_TYPE.get(domain_dir.name, domain_dir.name)
        txt_files = sorted(domain_dir.glob("*.txt"))

        if not txt_files:
            logger.warning("No .txt files found in %s — skipping.", domain_dir)
            continue

        logger.info(
            "Processing domain '%s' (%d files, clause_type=%s)…",
            domain_dir.name,
            len(txt_files),
            clause_type,
        )

        for txt_path in txt_files:
            try:
                record = parse_case_file(txt_path, clause_type)
                vector = model.encode(
                    record["text"], normalize_embeddings=True
                ).tolist()
                row_id = insert_precedent(conn, record, vector)
                logger.debug(
                    "  [%d] %s (%s, %s)",
                    row_id,
                    record["case_name"],
                    record["jurisdiction"],
                    record["year"],
                )
                inserted += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("  FAILED %s: %s", txt_path.name, exc)
                skipped += 1

    conn.close()

    logger.info(
        "Seeding complete. Inserted: %d | Skipped: %d | Total in table: %d",
        inserted,
        skipped,
        inserted,
    )
    return inserted


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Seed the legal precedent vector index in pgvector."
    )
    p.add_argument(
        "--dsn",
        default=os.environ.get("DATABASE_URL", ""),
        help="PostgreSQL DSN (default: $DATABASE_URL)",
    )
    p.add_argument(
        "--data-dir",
        default=str(
            Path(__file__).resolve().parent.parent
            / "data" / "precedents"
        ),
        help="Root of the precedents directory tree.",
    )
    p.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing precedent rows before seeding (idempotent).",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    if not args.dsn:
        logger.error(
            "No database DSN provided. Set DATABASE_URL or pass --dsn."
        )
        sys.exit(1)

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        logger.error("Data directory not found: %s", data_dir)
        sys.exit(1)

    total = seed(data_dir, args.dsn, reset=args.reset)

    if total < 50:
        logger.warning(
            "Only %d precedents were seeded; PRD requires at least 50.", total
        )
        sys.exit(2)

    print(f"\n✓  Successfully indexed {total} precedent cases into pgvector.")


if __name__ == "__main__":
    main()