import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from uuid import UUID
import ssl
from app.models.clause import Clause
from app.models.contract import Contract

DATABASE_URL = 'postgresql+asyncpg://neondb_owner:npg_knCUzXGvx0A8@ep-dark-glitter-am1oglls-pooler.c-5.us-east-1.aws.neon.tech/neondb'

async def run():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    engine = create_async_engine(DATABASE_URL, connect_args={"ssl": ssl_context}, echo=True)
    async with AsyncSession(engine) as db:
        clause_uuid = UUID('4350569e-1134-45b0-aacb-6b16d230b2fd')
        user_id = UUID('67a8111e-c620-4166-bd6b-6250f4ec9465')
        
        result = await db.execute(
            select(Clause)
            .join(Contract, Clause.contract_id == Contract.id)
            .where((Clause.id == clause_uuid) & (Contract.user_id == user_id))
        )
        clause = result.scalars().first()
        print('FastAPI Clause Result:', clause)
        
    await engine.dispose()

asyncio.run(run())
