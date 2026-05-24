import asyncio
import json
from services.api.app.db.session import SessionLocal
from sqlalchemy import text

async def main():
    async with SessionLocal() as db:
        res = await db.execute(text('SELECT id, status, progress_pct, error_message FROM scan_jobs ORDER BY created_at DESC LIMIT 5'))
        print(json.dumps([dict(row._mapping) for row in res.fetchall()], default=str))

asyncio.run(main())
