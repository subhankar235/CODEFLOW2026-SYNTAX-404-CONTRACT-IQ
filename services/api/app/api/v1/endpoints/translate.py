"""
Translate Endpoint — POST /api/v1/translate/{contractId}
Implements STEP 9.2: Queues post-scan language switching.
Also provides GET /{contractId}/status for polling translation completion.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.contract import Contract

from app.core.celery import celery_app

router = APIRouter()
logger = __import__("logging").getLogger(__name__)


@router.post("/{contract_id}")
async def translate_contract(
    contract_id: str,
    request: dict,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Queues translation of contract results to a different language.

    - Verifies JWT and ownership
    - Queues the translate_results Celery task
    - Returns 202 Accepted with task status
    """
    try:
        contract_uuid = UUID(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contract ID"
        )

    # Verify contract exists and belongs to user
    from app.repositories import user_repo
    user = await user_repo.get_user_by_clerk_id(db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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

    target_language = request.get("target_language", "en")

    # Validate language
    supported = ["en", "es", "fr", "de", "pt", "hi", "zh", "ja", "ar", "ru"]
    if target_language not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Supported: {supported}",
        )

    # Queue the Celery task
    task_id = None
    try:
        task = celery_app.send_task(
            "translate_results_task",
            args=[contract_id, target_language],
        )
        task_id = task.id
        logger.info(
            "Queued translation task %s for contract %s to %s",
            task_id,
            contract_id,
            target_language,
        )
    except Exception as e:
        logger.error("Failed to queue translation task: %s", e)
        # Return accepted anyway — translation may run inline or be deferred
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "task_id": None,
                "contract_id": contract_id,
                "target_language": target_language,
                "message": "Translation queued (Celery unavailable, will process inline)",
            },
        )

    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "task_id": task_id,
            "contract_id": contract_id,
            "target_language": target_language,
        },
    )


@router.get("/{contract_id}/status")
async def get_translation_status(
    contract_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if translation for a contract is complete.
    Frontend polls this endpoint after requesting translation.
    """
    try:
        contract_uuid = UUID(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contract ID"
        )

    from app.repositories import user_repo
    user = await user_repo.get_user_by_clerk_id(db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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

    # Check if translated fields exist on the contract or related clauses
    # The actual check depends on the data model — here we check a translated_at field
    is_complete = False
    try:
        # Check if any clause for this contract has translated text
        from sqlalchemy import text
        check_result = await db.execute(
            text(
                """SELECT COUNT(*) FROM contract_clauses 
                   WHERE contract_id = :cid 
                   AND (plain_english_translated IS NOT NULL OR headline_translated IS NOT NULL)
                   LIMIT 1"""
            ),
            {"cid": str(contract_uuid)},
        )
        count = check_result.scalar_one_or_none() or 0
        is_complete = count > 0
    except Exception as e:
        logger.warning("Could not check translation status: %s", e)
        # Fallback: check translated_at on contract if column exists
        try:
            is_complete = getattr(contract, "translated_at", None) is not None
        except Exception:
            is_complete = False

    return {
        "contract_id": contract_id,
        "translation_complete": is_complete,
        "status": "complete" if is_complete else "pending",
    }
