import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def check():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT id, original_filename FROM contracts ORDER BY created_at DESC LIMIT 3"))
        rows = res.fetchall()
        for r in rows:
            print(f"Contract: {r[1]} (ID: {r[0]})")
            clauses_res = await db.execute(text(f"SELECT position_index, text FROM clauses WHERE contract_id = '{r[0]}' ORDER BY position_index ASC LIMIT 2"))
            clauses = clauses_res.fetchall()
            for c in clauses:
                print(f"  Clause {c[0]}: {c[1][:100]}")

if __name__ == "__main__":
    asyncio.run(check())
