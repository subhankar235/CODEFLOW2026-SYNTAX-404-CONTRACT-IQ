from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_job import ScanJob


async def create(db: AsyncSession, scan_job: ScanJob) -> ScanJob:
    db.add(scan_job)
    await db.commit()
    await db.refresh(scan_job)
    return scan_job


async def get_by_id(db: AsyncSession, job_id: str) -> ScanJob | None:
    result = await db.execute(select(ScanJob).where(ScanJob.id == job_id))
    return result.scalar_one_or_none()


async def get_all_by_user_id(db: AsyncSession, user_id: str) -> list[ScanJob]:
    result = await db.execute(
        select(ScanJob).join(ScanJob.contract).where(ScanJob.contract.has(user_id=user_id))
        .order_by(ScanJob.created_at.desc())
    )
    return list(result.scalars().all())


async def update_status(db: AsyncSession, job_id: str, status: str) -> ScanJob | None:
    scan_job = await get_by_id(db, job_id)
    if scan_job:
        scan_job.status = status
        await db.commit()
        await db.refresh(scan_job)
    return scan_job


async def update_progress(db: AsyncSession, job_id: str, pct: int) -> ScanJob | None:
    scan_job = await get_by_id(db, job_id)
    if scan_job:
        scan_job.progress_pct = pct
        await db.commit()
        await db.refresh(scan_job)
    return scan_job


async def update(db: AsyncSession, scan_job: ScanJob) -> ScanJob:
    await db.commit()
    await db.refresh(scan_job)
    return scan_job


async def delete(db: AsyncSession, scan_job: ScanJob) -> None:
    await db.delete(scan_job)
    await db.commit()
