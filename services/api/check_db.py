import asyncio
<<<<<<< HEAD
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
        result = await conn.execute(text("SELECT id, contract_id FROM clauses WHERE id = '4350569e-1134-45b0-aacb-6b16d230b2fd'"))
        print('Clause:', result.fetchall())
        
        result2 = await conn.execute(text("SELECT id, user_id FROM contracts WHERE id = '4350569e-1134-45b0-aacb-6b16d230b2fd'"))
        print('Contract:', result2.fetchall())
        
    await engine.dispose()

asyncio.run(run())
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
