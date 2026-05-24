import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(r"c:\Users\subhankar nath\Desktop\Legal-Tech\.env")

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL not found in .env")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()
    
    print("Altering precedent_matches table...")
    
    # 1. Drop old columns if they exist
    cur.execute("ALTER TABLE precedent_matches DROP COLUMN IF EXISTS case_name;")
    cur.execute("ALTER TABLE precedent_matches DROP COLUMN IF EXISTS case_year;")
    cur.execute("ALTER TABLE precedent_matches DROP COLUMN IF EXISTS jurisdiction;")
    cur.execute("ALTER TABLE precedent_matches DROP COLUMN IF EXISTS outcome;")
    
    # 2. Add new columns
    cur.execute("ALTER TABLE precedent_matches ADD COLUMN IF NOT EXISTS precedent_summary TEXT;")
    cur.execute("ALTER TABLE precedent_matches ADD COLUMN IF NOT EXISTS cited_cases JSONB;")
    
    # Since SQLAlchemy has nullable=False, let's make sure they are NOT NULL. 
    # Because there are 0 rows, this will succeed.
    cur.execute("ALTER TABLE precedent_matches ALTER COLUMN precedent_summary SET NOT NULL;")
    cur.execute("ALTER TABLE precedent_matches ALTER COLUMN cited_cases SET NOT NULL;")
    
    conn.commit()
    print("Database schema successfully altered!")
    
    # Show new columns to verify
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'precedent_matches';")
    print("New columns in precedent_matches:")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")
        
    cur.close()
    conn.close()

except Exception as e:
    print("Error altering database:", e)
    if 'conn' in locals():
        conn.rollback()
