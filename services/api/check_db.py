import asyncio
from uuid import UUID
from sqlalchemy import text
from app.db.session import SessionLocal

async def check():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT id, original_filename, created_at FROM contracts ORDER BY created_at ASC"))
        rows = res.fetchall()
        print(f"Total contracts: {len(rows)}")
        for r in rows:
            print(f"- {r[1]} (ID: {r[0]})")
            
        res_clauses = await db.execute(text("SELECT contract_id, count(*) FROM clauses GROUP BY contract_id"))
        counts = res_clauses.fetchall()
        print("\nClause counts:")
        for c in counts:
            print(f"- Contract {c[0]}: {c[1]} clauses")

if __name__ == "__main__":
    asyncio.run(check())
