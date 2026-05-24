import asyncio
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
        result = await conn.execute(text("SELECT clauses.id FROM clauses JOIN contracts ON clauses.contract_id = contracts.id WHERE clauses.id = '4350569e-1134-45b0-aacb-6b16d230b2fd' AND contracts.user_id = '67a8111e-c620-4166-bd6b-6250f4ec9465'"))
        print('Query result:', result.fetchall())
        
    await engine.dispose()

asyncio.run(run())
