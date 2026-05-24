import asyncio
import json
from services.api.app.db.session import SessionLocal
from sqlalchemy import text

async def main():
    async with SessionLocal() as db:
        res = await db.execute(text('SELECT contract_id FROM scan_jobs ORDER BY created_at DESC LIMIT 1'))
        contract_id = res.scalar()
        res_clauses = await db.execute(text(f"SELECT COUNT(*) FROM clauses WHERE contract_id = '{contract_id}'"))
        print(f"Contract ID: {contract_id}, Clauses Count: {res_clauses.scalar()}")

asyncio.run(main())
