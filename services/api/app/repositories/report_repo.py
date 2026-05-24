"""Report repository — database query functions for reports."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.report import Report


async def create_report(
    session: AsyncSession,
    contract_id: UUID,
    file_path: str,
    share_uuid: str,
    share_expires_at: datetime,
) -> Report:
    """Create a new report."""
    report = Report(
        contract_id=contract_id,
        file_path=file_path,
        share_uuid=share_uuid,
        share_expires_at=share_expires_at,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


async def get_report_by_id(session: AsyncSession, report_id: UUID) -> Optional[Report]:
    """Get report by ID."""
    result = await session.execute(select(Report).where(Report.id == report_id))
    return result.scalars().first()


async def get_report_by_share_uuid(
    session: AsyncSession, share_uuid: str
) -> Optional[Report]:
    """Get report by share UUID (for public sharing)."""
    result = await session.execute(
        select(Report).where(Report.share_uuid == share_uuid)
    )
    return result.scalars().first()


async def get_report_by_contract_id(
    session: AsyncSession, contract_id: UUID
) -> Optional[Report]:
    """Get most recent report for a contract."""
    result = await session.execute(
        select(Report)
        .where(Report.contract_id == contract_id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


async def delete_report(session: AsyncSession, report_id: UUID) -> bool:
    """Delete a report."""
    report = await get_report_by_id(session, report_id)
    if not report:
        return False

    await session.delete(report)
    await session.commit()
    return True


async def delete_expired_reports(session: AsyncSession) -> int:
    """Delete all expired share links and return count deleted."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    result = await session.execute(select(Report).where(Report.share_expires_at <= now))
    expired_reports = result.scalars().all()

    for report in expired_reports:
        await session.delete(report)

    await session.commit()
    return len(expired_reports)
