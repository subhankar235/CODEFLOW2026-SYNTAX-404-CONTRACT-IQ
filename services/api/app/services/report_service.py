import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.models.contract import Contract


async def create_report_record(
    db: AsyncSession, contract_id: uuid.UUID, file_path: str, expiry_hours: int = 48
) -> Report:
    """Create a new report record with a share link."""
    share_uuid = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

    report = Report(
        contract_id=contract_id,
        file_path=file_path,
        share_uuid=share_uuid,
        share_expires_at=expires_at,
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_report_by_id(
    db: AsyncSession, report_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Report]:
    """Get a report by ID and verify user ownership of the contract."""
    query = (
        select(Report)
        .join(Contract)
        .where(Report.id == report_id)
        .where(Contract.user_id == user_id)
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_report_by_share_uuid(
    db: AsyncSession, share_uuid: str
) -> Optional[Report]:
    """Get a report by share UUID and check for expiry."""
    query = select(Report).where(Report.share_uuid == share_uuid)
    result = await db.execute(query)
    report = result.scalars().first()

    if not report:
        return None

    # Check expiry
    if report.share_expires_at < datetime.now(timezone.utc):
        return None

    return report


async def get_all_reports_for_contract(
    db: AsyncSession, contract_id: uuid.UUID
) -> List[Report]:
    """Get all reports for a specific contract."""
    query = (
        select(Report)
        .where(Report.contract_id == contract_id)
        .order_by(Report.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


async def delete_expired_reports(db: AsyncSession) -> int:
    """Delete all expired reports from the database."""
    now = datetime.now(timezone.utc)
    query = select(Report).where(Report.share_expires_at < now)
    result = await db.execute(query)
    expired_reports = result.scalars().all()

    count = 0
    for report in expired_reports:
        # Note: Physical file deletion should be handled by the caller or a utility
        await db.delete(report)
        count += 1

    await db.commit()
    return count
