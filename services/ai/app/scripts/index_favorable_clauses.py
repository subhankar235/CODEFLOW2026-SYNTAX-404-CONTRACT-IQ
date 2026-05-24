#!/usr/bin/env python3
"""Seed favorable clause variants into embeddings table."""
import os
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("index_favorable_clauses")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "services" / "ai" / "app" / "data" / "favorable_clauses"
EMBEDDING_TYPE = "favorable_clause"


def ensure_embeddings_table(conn):
    """Verify embeddings table exists."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'embeddings'
            );
        """)
        if not cur.fetchone()[0]:
            raise RuntimeError("embeddings table does not exist. Run migrations first.")
    logger.info("embeddings table verified.")


def reset_favorable_clauses(conn):
    """Delete existing favorable_clause records."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM embeddings WHERE embedding_type = %s RETURNING id;", (EMBEDDING_TYPE,))
        deleted = cur.rowcount
        conn.commit()
    logger.info("Deleted %d existing favorable clause records.", deleted)
    return deleted


def insert_favorable_clause(conn, record: dict, vector: list[float]) -> str:
    """Insert one favorable clause and return its id."""
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
        "clause_type": record["clause_type"],
        "variant": record["variant"],
        "filename": record["filename"],
    }
    with conn.cursor() as cur:
        cur.execute(sql, (row_id, EMBEDDING_TYPE, record["text"], vector_str, json.dumps(metadata)))
        conn.commit()
    return row_id


def discover_variants(data_dir: Path):
    """Find all variant files."""
    variants = []
    for clause_dir in sorted(data_dir.iterdir()):
        if not clause_dir.is_dir():
            continue
        clause_type = clause_dir.name
        for fp in sorted(clause_dir.glob("*.txt")):
            text = fp.read_text(encoding="utf-8").strip()
            if text:
                variants.append({
                    "clause_type": clause_type,
                    "variant": fp.stem,
                    "filename": fp.name,
                    "text": text,
                })
    return variants


def run(data_dir: Path, reset: bool = False):
    """Index all favorable clause variants."""
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        logger.error("DATABASE_URL not set")
        return 0
    
    conn = psycopg2.connect(dsn)
    ensure_embeddings_table(conn)
    
    if reset:
        reset_favorable_clauses(conn)
    
    variants = discover_variants(data_dir)
    logger.info("Found %d variant files across %d clause types", len(variants), len({v["clause_type"] for v in variants}))
    
    if not variants:
        logger.error("No variants found")
        return 0
    
    logger.info("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    inserted = 0
    for record in variants:
        vector = model.encode(record["text"], normalize_embeddings=True).tolist()
        row_id = insert_favorable_clause(conn, record, vector)
        logger.debug("Indexed: %s / %s", record["clause_type"], record["variant"])
        inserted += 1
    
    logger.info("Seeding complete. Inserted: %d | Total in table: %d", inserted, inserted)
    conn.close()
    return inserted


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed favorable clause variants.")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Data directory")
    parser.add_argument("--reset", action="store_true", help="Reset existing records")
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error("Data directory not found: %s", data_dir)
    else:
        run(data_dir, reset=args.reset)