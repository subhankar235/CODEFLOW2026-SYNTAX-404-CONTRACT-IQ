import asyncio
from sqlalchemy import text
from services.api.app.db.session import SessionLocal

async def main():
    async with SessionLocal() as db:
        await db.execute(text('ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS context_data JSONB;'))
        await db.commit()
        print("Column context_data added to embeddings.")

asyncio.run(main())
