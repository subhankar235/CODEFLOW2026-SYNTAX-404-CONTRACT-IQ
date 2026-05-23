from datetime import datetime, timezone

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


async def create(db: AsyncSession, report: Report) -> Report:
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_by_id(db: AsyncSession, report_id: str) -> Report | None:
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


async def get_by_share_uuid(db: AsyncSession, share_uuid: str) -> Report | None:
    result = await db.execute(select(Report).where(Report.share_uuid == share_uuid))
    return result.scalar_one_or_none()


async def get_all_by_user_id(db: AsyncSession, user_id: str) -> list[Report]:
    result = await db.execute(
        select(Report).join(Report.contract).where(Report.contract.has(user_id=user_id))
        .order_by(Report.created_at.desc())
    )
    return list(result.scalars().all())


async def update(db: AsyncSession, report: Report) -> Report:
    await db.commit()
    await db.refresh(report)
    return report


async def delete(db: AsyncSession, report: Report) -> None:
    await db.delete(report)
    await db.commit()


async def delete_expired(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        sa_delete(Report).where(Report.expires_at < now).returning(Report.id)
    )
    await db.commit()
    return len(result.scalars().all())
