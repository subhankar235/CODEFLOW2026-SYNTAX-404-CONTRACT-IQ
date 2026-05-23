from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract


async def create(db: AsyncSession, contract: Contract) -> Contract:
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


async def get_by_id(db: AsyncSession, contract_id: str) -> Contract | None:
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    return result.scalar_one_or_none()


async def get_all_by_user_id(db: AsyncSession, user_id: str) -> list[Contract]:
    result = await db.execute(
        select(Contract).where(Contract.user_id == user_id).order_by(Contract.created_at.desc())
    )
    return list(result.scalars().all())


async def update(db: AsyncSession, contract: Contract) -> Contract:
    await db.commit()
    await db.refresh(contract)
    return contract


async def delete(db: AsyncSession, contract: Contract) -> None:
    await db.delete(contract)
    await db.commit()
