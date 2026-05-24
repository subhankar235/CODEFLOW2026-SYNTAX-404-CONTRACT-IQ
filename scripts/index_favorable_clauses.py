import os
import json
import uuid
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

def index_favorable_clauses():
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/legal_tech")
    db_url = db_url.replace("postgresql+asyncpg", "postgresql")
    
    base_dir = Path("services/ai/data/favorable_clauses")
    if not base_dir.exists():
        print("Favorable clauses directory does not exist.")
        return

    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    rows = []
    
    for folder in base_dir.iterdir():
        if folder.is_dir():
            for file_path in folder.glob("*.json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                clause_type = data.get("clause_type", "unknown")
                favorable_text = data.get("favorable_text", "")
                
                embedding = model.encode(favorable_text, convert_to_numpy=True).tolist()
                embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
                
                context_data = json.dumps({
                    "clause_type": clause_type,
                    "domain": data.get("domain", ""),
                    "explanation": data.get("explanation", "")
                })
                
                rows.append((
                    str(uuid.uuid4()), # id
                    None,                 # contract_id
                    None,                 # clause_id
                    "favorable_clause",   # embedding_type
                    favorable_text,       # text
                    embedding_str,        # embedding
                    context_data          # context_data
                ))

    if not rows:
        print("No favorable clauses to index.")
        return

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM embeddings WHERE embedding_type = 'favorable_clause';")
            
            execute_values(
                cur,
                """INSERT INTO embeddings (id, contract_id, clause_id, embedding_type, text, embedding, context_data)
                   VALUES %s""",
                rows,
                template="(%s, %s, %s, %s, %s, %s::vector, %s::jsonb)"
            )
        conn.commit()

    print(f"Successfully indexed {len(rows)} favorable clauses.")

if __name__ == "__main__":
    index_favorable_clauses()
