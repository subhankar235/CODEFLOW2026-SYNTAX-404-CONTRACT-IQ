"""
Precedent Endpoint — GET /api/v1/precedent/{clauseId}
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import httpx
import os

from app.api.deps import get_current_user, get_db
from app.models.clause import Clause
from app.models.contract import Contract
from app.models.precedent_match import PrecedentMatch
from sqlalchemy import select

router = APIRouter()

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")


@router.get("/{clause_id}")
async def get_precedent(
    clause_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns legal precedent for a specific clause.
    For demo clause IDs, calls the AI service for real AI-generated analysis.
    """
    if clause_id.startswith("clause-"):
        clause_map = {
            "clause-001": {"clause_text": "The Employee agrees that during the term of employment and for a period of two (2) years following termination, the Employee shall not engage in any business that competes directly or indirectly with the Employer within a radius of fifty (50) miles of any of the Employer's offices.", "clause_type": "non_compete", "risk_category": "non_compete"},
            "clause-002": {"clause_text": "All intellectual property, including but not limited to inventions, discoveries, improvements, designs, works of authorship, and trade secrets, conceived, developed, or reduced to practice by the Employee during the term of employment, whether during working hours or using company resources or not, shall be the sole and exclusive property of the Company.", "clause_type": "ip_assignment", "risk_category": "ip_assignment"},
            "clause-003": {"clause_text": "The Company may terminate this Agreement at any time, with or without cause, without prior notice, and without any severance obligation. The Employee hereby waives any right to advance notice, severance pay, or any other compensation upon termination.", "clause_type": "termination", "risk_category": "termination"},
            "clause-004": {"clause_text": "The Employee agrees to assign to the Company all rights, title, and interest in any patents, copyrights, trademarks, or other intellectual property rights arising from work performed using company time, equipment, facilities, or resources, including but not limited to pre-existing IP that is incorporated into company products.", "clause_type": "ip_assignment", "risk_category": "ip_assignment"},
            "clause-005": {"clause_text": "The Employee shall indemnify and hold harmless the Company from any claims, damages, losses, or expenses (including reasonable attorney fees) arising from the Employee's breach of this Agreement, negligence, or willful misconduct, whether by action or omission.", "clause_type": "indemnity", "risk_category": "indemnity"},
            "clause-006": {"clause_text": "This agreement shall automatically renew for successive one (1) year periods unless either party provides written notice of non-renewal at least sixty (60) days prior to the end of the then-current term.", "clause_type": "auto_renewal", "risk_category": "auto_renewal"},
            "clause-007": {"clause_text": "The Employee acknowledges and agrees that the total liability of the Company under this Agreement, whether in contract, tort, or otherwise, shall not exceed the total fees paid by the Company to the Employee in the twelve (12) months preceding the claim.", "clause_type": "limitation_of_liability", "risk_category": "limitation_of_liability"},
            "clause-008": {"clause_text": "Payment terms: Net 30 days from invoice date. Late payments shall accrue interest at a rate of 1.5% per month (18% APR) on the outstanding balance.", "clause_type": "payment", "risk_category": "payment"},
            "clause-009": {"clause_text": "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to its conflict of laws principles.", "clause_type": "governing_law", "risk_category": "governing_law"},
            "clause-010": {"clause_text": "Any notice required or permitted under this Agreement shall be in writing and delivered by email to the addresses provided by each party. Email shall constitute valid delivery for all purposes under this Agreement.", "clause_type": "other", "risk_category": "other"},
        }
        
        clause_info = clause_map.get(clause_id, clause_map.get("clause-001", {}))
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{AI_SERVICE_URL}/api/v1/precedent",
                    json={
                        "clause_text": clause_info.get("clause_text", ""),
                        "clause_type": clause_info.get("clause_type", "other"),
                        "risk_category": clause_info.get("risk_category", "other"),
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return JSONResponse(
                        status_code=200,
                        content={
                            "clause_id": clause_id,
                            "status": "ready",
                            "precedent_summary": data.get("precedent_summary", ""),
                            "enforcement_likelihood": data.get("enforcement_likelihood", "Uncertain"),
                            "confidence_score": data.get("confidence_score", 60),
                            "cited_cases": data.get("cited_cases", []),
                        },
                    )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("AI service call failed for precedent demo: %s", e)
        
        return JSONResponse(
            status_code=200,
            content={"clause_id": clause_id, "status": "ready"},
        )

    try:
        clause_uuid = UUID(clause_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clause ID"
        )

    # Verify clause exists and contract belongs to user
    from app.repositories import user_repo
    user = await user_repo.get_user_by_clerk_id(db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where((Clause.id == clause_uuid) & (Contract.user_id == user.id))
    )
    clause = result.scalars().first()

    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clause not found or access denied",
        )

    result = await db.execute(
        select(PrecedentMatch).where(PrecedentMatch.clause_id == clause_uuid)
    )
    precedent = result.scalars().first()

    if not precedent:
        # Generate on-the-fly using the AI service for clauses without a precedent match
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Generating on-the-fly precedent for clause {clause_id} via {AI_SERVICE_URL}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{AI_SERVICE_URL}/api/v1/precedent",
                    json={
                        "clause_text": clause.text,
                        "clause_type": clause.risk_category or "other",
                        "risk_category": clause.risk_category or "other",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # Store it for next time
                    import uuid
                    new_precedent = PrecedentMatch(
                        clause_id=clause.id,
                        precedent_summary=data.get("precedent_summary", ""),
                        enforcement_likelihood=data.get("enforcement_likelihood", "Uncertain"),
                        confidence_score=data.get("confidence_score", 60),
                        cited_cases=data.get("cited_cases", [])
                    )
                    db.add(new_precedent)
                    await db.commit()
                    
                    return JSONResponse(
                        status_code=200,
                        content={
                            "clause_id": clause_id,
                            "status": "ready",
                            "precedent_summary": data.get("precedent_summary", ""),
                            "enforcement_likelihood": data.get("enforcement_likelihood", "Uncertain"),
                            "confidence_score": data.get("confidence_score", 60),
                            "cited_cases": data.get("cited_cases", []),
                        },
                    )
                else:
                    logger.warning(f"AI service returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("AI service call failed for on-the-fly precedent: %s", e)

        # Fallback if AI call fails
        return JSONResponse(
            status_code=200,
            content={
                "clause_id": clause_id,
                "status": "ready",
                "precedent_summary": "No precedents could be automatically generated for this clause at this time.",
                "enforcement_likelihood": "Uncertain",
                "confidence_score": 0,
                "cited_cases": [],
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "clause_id": str(precedent.clause_id),
            "precedent_summary": precedent.precedent_summary,
            "enforcement_likelihood": precedent.enforcement_likelihood,
            "confidence_score": precedent.confidence_score,
            "cited_cases": precedent.cited_cases,
        },
    )