import asyncio
<<<<<<< HEAD
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
=======
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import ssl

DATABASE_URL = 'postgresql+asyncpg://neondb_owner:npg_knCUzXGvx0A8@ep-dark-glitter-am1oglls-pooler.c-5.us-east-1.aws.neon.tech/neondb'

async def run():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    engine = create_async_engine(DATABASE_URL, connect_args={"ssl": ssl_context})
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, user_id FROM contracts WHERE id = '0077d290-cd4e-4abf-a417-a36b93fbbfd3'"))
        print('Contract for clause:', result.fetchall())
        
    await engine.dispose()

asyncio.run(run())
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
