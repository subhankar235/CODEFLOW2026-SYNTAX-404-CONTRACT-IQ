from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import os

from app.db.session import get_async_session
from app.core.security import get_current_user_id
from app.repositories import contract_repo, user_repo
from app.services import report_service
from app.core.celery import celery_app

router = APIRouter()


@router.post("/generate/{contractId}")
async def generate_report(
    contractId: UUID,
    language: str = "en",
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Verify ownership, create a report record, and queue the generation task.
    """
    # 1. Get internal user
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Verify contract ownership
    contract = await contract_repo.get_contract_by_id(db, contractId, user.id)
    if not contract:
        raise HTTPException(
            status_code=404, detail="Contract not found or access denied"
        )

    # 3. Create report record
    # file_path is initially empty, will be updated by the worker
    report = await report_service.create_report_record(
        db, contract_id=contractId, file_path="", expiry_hours=48
    )

    # 4. Queue Celery task
    celery_app.send_task(
        "generate_report", args=[str(contractId), str(report.id), language]
    )

    return {
        "message": "Report generation started",
        "report_id": str(report.id),
        "status": "processing",
    }


@router.get("/{reportId}")
async def get_report(
    reportId: UUID,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Retrieve report details or download the PDF if it exists.
    """
    # 1. Get internal user
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get report and verify ownership
    report = await report_service.get_report_by_id(db, reportId, user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or access denied")

    if not report.file_path or not os.path.exists(report.file_path):
        return {
            "report_id": str(report.id),
            "status": "processing",
            "message": "Report is still being generated",
        }

    # Generate public share URL
    share_url = f"/api/v1/report/share/{report.share_uuid}"

    return {
        "report_id": str(report.id),
        "contract_id": str(report.contract_id),
        "status": "complete",
        "share_url": share_url,
        "expires_at": report.share_expires_at.isoformat(),
        "download_url": f"/api/v1/report/download/{report.id}",  # Internal download
    }


@router.get("/download/{reportId}")
async def download_report(
    reportId: UUID,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """Internal download link for the authenticated user."""
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404)

    report = await report_service.get_report_by_id(db, reportId, user.id)
    if not report or not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=f"report_{reportId}.pdf",
    )


@router.get("/share/{shareUuid}")
async def get_shared_report(
    shareUuid: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Public endpoint to access a report via share UUID.
    Checks for expiry.
    """
    report = await report_service.get_report_by_share_uuid(db, shareUuid)

    if not report:
        # Check if it exists but is expired
        from app.repositories import report_repo

        expired_report = await report_repo.get_report_by_share_uuid(db, shareUuid)
        if expired_report:
            raise HTTPException(status_code=410, detail="This share link has expired")
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=202, detail="Report is still being generated")

    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=f"shared_report_{shareUuid[:8]}.pdf",
    )
