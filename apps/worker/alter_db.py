import asyncio
from sqlalchemy import text
from services.api.app.db.session import SessionLocal

async def main():
    async with SessionLocal() as db:
        await db.execute(text('ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS one_liner VARCHAR;'))
        await db.commit()
        print("Column one_liner added to analysis_results.")

asyncio.run(main())
