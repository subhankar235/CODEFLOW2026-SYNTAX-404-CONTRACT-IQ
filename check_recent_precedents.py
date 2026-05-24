import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.api.app.db.session import SessionLocal
from services.api.app.models.precedent_match import PrecedentMatch
from sqlalchemy import select

async def main():
    async with SessionLocal() as db:
        result = await db.execute(
            select(PrecedentMatch).order_by(PrecedentMatch.created_at.desc()).limit(5)
        )
        matches = result.scalars().all()
        if not matches:
            print("No precedents found in the database at all!")
        else:
            for m in matches:
                print(f"Precedent generated at {m.created_at} for clause {m.clause_id}")

if __name__ == "__main__":
    asyncio.run(main())
