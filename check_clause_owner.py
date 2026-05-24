import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.api.app.db.session import SessionLocal
from services.api.app.models.clause import Clause
from services.api.app.models.contract import Contract
from sqlalchemy import select

async def main():
    clause_id = "0cd5a6dd-1eff-4cca-bb34-62c9be98e726"
    async with SessionLocal() as db:
        result = await db.execute(
            select(Clause, Contract).join(Contract, Clause.contract_id == Contract.id).where(Clause.id == clause_id)
        )
        row = result.first()
        if not row:
            print(f"Clause {clause_id} does not exist at all in the database!")
        else:
            clause, contract = row
            print(f"Clause found!")
            print(f"Contract ID: {contract.id}")
            print(f"Contract user_id: {contract.user_id}")
            
            # Also get the current user's ID
            from services.api.app.models.user import User
            user_result = await db.execute(select(User).where(User.clerk_user_id == "user_3DVMqKAfAAHnJAt2FYuHMCqJxvX"))
            user = user_result.scalars().first()
            if user:
                print(f"User UUID in DB: {user.id}")
                if str(user.id) == str(contract.user_id):
                    print("MATCH! The user_id matches the contract.user_id. The query should not fail.")
                else:
                    print("MISMATCH! The contract belongs to someone else!")
            else:
                print("User not found in DB!")

if __name__ == "__main__":
    asyncio.run(main())
