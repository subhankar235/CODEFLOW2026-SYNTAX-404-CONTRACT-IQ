"""
Power Asymmetry Endpoint — GET /api/v1/power/{contractId}
Implements STEP 7.2: Returns power asymmetry analysis for a completed scan.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_async_session
from app.core.security import get_current_user_id
from app.repositories import user_repo
from app.models.contract import Contract
from app.models.analysis_result import AnalysisResult
from sqlalchemy import select

router = APIRouter()


@router.get("/{contract_id}")
async def get_power_analysis(
    contract_id: str,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Returns the power asymmetry analysis for a contract.
    """
    # Auto-create user if not exists
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        user = await user_repo.create_user(
            session=db,
            clerk_user_id=user_id,
            email=f"{user_id}@placeholder.local",
        )
        await db.commit()
        await db.refresh(user)

    try:
        contract_uuid = UUID(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contract ID"
        )

    # Verify contract exists and belongs to user
    result = await db.execute(
        select(Contract).where(
            (Contract.id == contract_uuid) & (Contract.user_id == user.id)
        )
    )
    contract = result.scalars().first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found or access denied",
        )

    # Fetch analysis result
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.contract_id == contract_uuid)
    )
    analysis = result.scalars().first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Analysis not yet available",
        )

    # Return power analysis fields
    return JSONResponse(
        status_code=200,
        content={
            "contract_id": str(analysis.contract_id),
            "power_score": analysis.power_score or 0,
            "power_label": analysis.power_label or "Unknown",
            "key_imbalances": [
                {"clause": lp, "why": "Power asymmetry detected", "score": analysis.power_score or 0}
                for lp in (analysis.leverage_points or [])
            ],
            "leverage_points": analysis.leverage_points or [],
        },
    )
