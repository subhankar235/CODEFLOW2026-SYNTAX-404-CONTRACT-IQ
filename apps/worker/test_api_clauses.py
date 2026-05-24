import asyncio
import json
from services.api.app.db.session import SessionLocal
from services.api.app.repositories import clause_repo

async def main():
    async with SessionLocal() as db:
        clauses = await clause_repo.get_all_clauses_by_contract_id(db, '8a0f9319-d1b7-484d-9908-3102fd75055b')
        result = [
            {
                "id": str(cl.id),
                "contract_id": str(cl.contract_id),
                "text": cl.text,
                "position_index": cl.position_index,
                "risk_level": cl.risk_level,
                "risk_category": cl.risk_category,
                "plain_english": cl.plain_english,
                "worst_case": cl.worst_case_scenario,
                "financial_exposure": cl.financial_exposure,
                "negotiable": cl.negotiable,
                "confidence": cl.confidence,
            }
            for cl in clauses
        ]
        print(json.dumps(result, indent=2))

asyncio.run(main())
