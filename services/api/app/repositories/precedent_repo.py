from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.precedent_match import PrecedentMatch


async def create(db: AsyncSession, match: PrecedentMatch) -> PrecedentMatch:
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


async def bulk_create(db: AsyncSession, matches: list[PrecedentMatch]) -> list[PrecedentMatch]:
    db.add_all(matches)
    await db.commit()
    for m in matches:
        await db.refresh(m)
    return matches


async def get_by_id(db: AsyncSession, match_id: str) -> PrecedentMatch | None:
    result = await db.execute(select(PrecedentMatch).where(PrecedentMatch.id == match_id))
    return result.scalar_one_or_none()


async def get_all_by_clause_id(db: AsyncSession, clause_id: str) -> list[PrecedentMatch]:
    result = await db.execute(
        select(PrecedentMatch).where(PrecedentMatch.clause_id == clause_id)
    )
    return list(result.scalars().all())


async def update(db: AsyncSession, match: PrecedentMatch) -> PrecedentMatch:
    await db.commit()
    await db.refresh(match)
    return match


async def delete(db: AsyncSession, match: PrecedentMatch) -> None:
    await db.delete(match)
    await db.commit()
