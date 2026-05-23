from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clause import Clause


async def create(db: AsyncSession, clause: Clause) -> Clause:
    db.add(clause)
    await db.commit()
    await db.refresh(clause)
    return clause


async def bulk_create(db: AsyncSession, clauses: list[Clause]) -> list[Clause]:
    db.add_all(clauses)
    await db.commit()
    for c in clauses:
        await db.refresh(c)
    return clauses


async def get_by_id(db: AsyncSession, clause_id: str) -> Clause | None:
    result = await db.execute(select(Clause).where(Clause.id == clause_id))
    return result.scalar_one_or_none()


async def get_all_by_contract_id(db: AsyncSession, contract_id: str) -> list[Clause]:
    result = await db.execute(
        select(Clause).where(Clause.contract_id == contract_id).order_by(Clause.position_index)
    )
    return list(result.scalars().all())


async def update(db: AsyncSession, clause: Clause) -> Clause:
    await db.commit()
    await db.refresh(clause)
    return clause


async def delete(db: AsyncSession, clause: Clause) -> None:
    await db.delete(clause)
    await db.commit()
