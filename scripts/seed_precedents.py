import os
import json
import uuid
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

def seed_precedents():
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/legal_tech")
    db_url = db_url.replace("postgresql+asyncpg", "postgresql")
    
    base_dir = Path("services/ai/data/precedents")
    if not base_dir.exists():
        print("Precedents directory does not exist.")
        return

    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    rows = []
    
    # Iterate through each folder and read json files
    for folder in base_dir.iterdir():
        if folder.is_dir():
            for file_path in folder.glob("*.json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                clause_type = data.get("clause_type", "unknown")
                # Create a search text that represents the case
                search_text = f"{data['summary']} {data['outcome']}"
                
                embedding = model.encode(search_text, convert_to_numpy=True).tolist()
                embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
                
                context_data = json.dumps({
                    "case_name": data.get("case_name", ""),
                    "year": data.get("year", 0),
                    "jurisdiction": data.get("jurisdiction", ""),
                    "outcome": data.get("outcome", ""),
                    "clause_type": clause_type,
                    "summary": data.get("summary", "")
                })
                
                rows.append((
                    str(uuid.uuid4()), # id
                    None,           # contract_id
                    None,           # clause_id
                    "precedent",    # embedding_type
                    search_text,    # text
                    embedding_str,  # embedding
                    context_data    # context_data
                ))

    if not rows:
        print("No precedents to index.")
        return

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Delete existing precedents to avoid duplicates during re-runs
            cur.execute("DELETE FROM embeddings WHERE embedding_type = 'precedent';")
            
            execute_values(
                cur,
                """INSERT INTO embeddings (id, contract_id, clause_id, embedding_type, text, embedding, context_data)
                   VALUES %s""",
                rows,
                template="(%s, %s, %s, %s, %s, %s::vector, %s::jsonb)"
            )
        conn.commit()

    print(f"Successfully indexed {len(rows)} legal precedents.")

if __name__ == "__main__":
    seed_precedents()
