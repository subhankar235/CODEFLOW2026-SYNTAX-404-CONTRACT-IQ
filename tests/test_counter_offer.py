#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from sentence_transformers import SentenceTransformer
import json

def test_step_7_6():
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        print("ERROR: DATABASE_URL not set")
        return
    
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    
    print("=" * 60)
    print("STEP 7.6 - Seeding Favorable Clauses")
    print("=" * 60)
    
    # Clean and seed
    cur.execute("DELETE FROM embeddings WHERE embedding_type = 'favorable_clause'")
    conn.commit()
    print("Cleared existing favorable clauses")
    
    data_dir = Path("services/ai/app/data/favorable_clauses")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    variants = []
    for clause_dir in sorted(data_dir.iterdir()):
        if clause_dir.is_dir():
            clause_type = clause_dir.name
            for fp in sorted(clause_dir.glob("*.txt")):
                text = fp.read_text(encoding="utf-8").strip()
                if text:
                    variants.append({"clause_type": clause_type, "variant": fp.stem, "text": text})
    
    print(f"Found {len(variants)} variant files")
    
    for v in variants:
        vector = model.encode(v["text"], normalize_embeddings=True).tolist()
        vector_str = "[" + ",".join(f"{x:.8f}" for x in vector) + "]"
        metadata = json.dumps({"clause_type": v["clause_type"], "variant": v["variant"]})
        cur.execute(
            "INSERT INTO embeddings (id, embedding_type, text, embedding, metadata) VALUES (gen_random_uuid(), 'favorable_clause', %s, %s::vector, %s)",
            (v["text"], vector_str, metadata)
        )
        conn.commit()
    
    print(f"Inserted {len(variants)} favorable clauses")
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_type = 'favorable_clause'")
    total = cur.fetchone()[0]
    print(f"Total favorable clauses in DB: {total}")
    
    cur.execute("""
        SELECT metadata->>'clause_type' as type, COUNT(*) 
        FROM embeddings WHERE embedding_type = 'favorable_clause' 
        GROUP BY type
    """)
    print("\nBy clause_type:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    print("\n" + "=" * 60)
    print("STEP 7.6 - Testing Retrieval")
    print("=" * 60)
    
    # Test retrieval
    test_clause = """
    All inventions, developments, and works of authorship conceived by Employee 
    during employment shall be the sole property of Company. Employee hereby assigns 
    all rights, title, and interest in such intellectual property to Company.
    """
    
    embedding = model.encode(test_clause).tolist()
    vector_str = "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"
    
    cur.execute("""
        SELECT text, metadata, 1 - (embedding <=> CAST(%s AS vector)) as similarity
        FROM embeddings
        WHERE embedding_type = 'favorable_clause'
          AND metadata->>'clause_type' = 'ip_assignment'
        ORDER BY embedding <=> CAST(%s AS vector)
        LIMIT 3
    """, (vector_str, vector_str))
    
    results = cur.fetchall()
    print("\nIP Assignment clause retrieval:")
    for row in results:
        meta = row[1]
        print(f"  Sim: {row[2]:.3f} | {meta.get('variant', 'N/A')} ({meta.get('clause_type', 'N/A')})")
    
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print(f"[{'PASS' if total >= 25 else 'FAIL'}] Favorable clauses seeded: {total} (min: 25)")
    print(f"[{'PASS' if len(results) >= 1 else 'FAIL'}] IP retrieval returns results: {len(results)}")
    
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    test_step_7_6()