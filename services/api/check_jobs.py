import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def check():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT contracts.original_filename, scan_jobs.status, scan_jobs.error_message, contracts.id FROM scan_jobs JOIN contracts ON scan_jobs.contract_id = contracts.id ORDER BY scan_jobs.created_at DESC LIMIT 5"))
        rows = res.fetchall()
        print("Recent scan jobs:")
        for r in rows:
            print(f"- {r[0]}: {r[1]} (Error: {r[2]}) [ID: {r[3]}]")
            
        print("\nClause counts for these contracts:")
        for r in rows:
            c_res = await db.execute(text(f"SELECT count(*) FROM clauses WHERE contract_id = '{r[3]}'"))
            c_count = c_res.scalar()
            print(f"- {r[0]}: {c_count} clauses")

if __name__ == "__main__":
    asyncio.run(check())
