#!/usr/bin/env python
"""Test precedent retrieval with specific clauses."""
import os
from dotenv import load_dotenv
load_dotenv()

import psycopg2
from sentence_transformers import SentenceTransformer

dsn = os.getenv("DATABASE_URL", "")
conn = psycopg2.connect(dsn)
cur = conn.cursor()

print("=" * 60)
print("STEP 7.4 - Testing with SPECIFIC clauses")
print("=" * 60)

model = SentenceTransformer("all-MiniLM-L6-v2")

test_clauses = {
    "non_compete": """
During employment and for 12 months thereafter, Employee shall not directly or indirectly
solicit any customers or employees of Employer, nor engage in any business competing
with Employer within 50 miles. Employee acknowledges receiving substantial compensation
and training that constitute valid consideration for this restriction.
""",
    "ip_assignment": """
All inventions, discoveries, developments, and works of authorship conceived,
reduced to practice, or made by Employee during employment, whether during
working hours or using Company resources, shall be the sole property of Company.
Employee hereby assigns all rights, title, and interest in such intellectual property to Company.
""",
    "nda": """
Employee agrees to hold in strict confidence all Confidential Information received
from Company. Confidential Information includes but is not limited to trade secrets,
technical data, business plans, customer lists, and financial information.
Employee shall not disclose or use any Confidential Information for any purpose
without prior written consent from Company.
"""
}

for clause_type, clause_text in test_clauses.items():
    print(f"\n--- Testing {clause_type.upper()} clause ---")
    embedding = model.encode(clause_text).tolist()
    vector_str = "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"

    cur.execute("""
        SELECT text, metadata, 1 - (embedding <=> CAST(%s AS vector)) as similarity
        FROM embeddings
        WHERE embedding_type = 'precedent'
          AND metadata->>'clause_type' = %s
        ORDER BY embedding <=> CAST(%s AS vector)
        LIMIT 3
    """, (vector_str, clause_type, vector_str))

    results = cur.fetchall()
    if results:
        similarities = []
        for row in results:
            sim = row[2]
            meta = row[1]
            print(f"  Sim: {sim:.3f} | {meta.get('case_name', 'N/A')} ({meta.get('year', 'N/A')})")
            similarities.append(sim)
        avg = sum(similarities) / len(similarities)
        print(f"  Avg similarity: {avg:.3f}")
    else:
        print("  No results found!")

print("\n" + "=" * 60)
print("STEP 7.5 - Seeding Verification")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_type = 'precedent'")
print(f"Total precedents: {cur.fetchone()[0]}")

print("\n" + "=" * 60)
print("STEP 7.4 - Confidence Score")
print("=" * 60)
print("Formula: score = similarity * (llm_confidence/100) * 100")
print("Test: 0.7 similarity * 80 confidence =", round(0.7 * 0.8 * 100, 2))

conn.close()
print("\n✅ All tests completed!")