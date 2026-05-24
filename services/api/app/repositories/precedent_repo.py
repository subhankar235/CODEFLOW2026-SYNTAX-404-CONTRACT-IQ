"""Precedent repository — database query functions for legal precedents."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.precedent_match import PrecedentMatch


async def create_precedent_match(
    session: AsyncSession,
    clause_id: UUID,
    case_name: str,
    case_year: int,
    jurisdiction: str,
    outcome: str,
    enforcement_likelihood: str,
    confidence_score: float,
) -> PrecedentMatch:
    """Create a new precedent match."""
    match = PrecedentMatch(
        clause_id=clause_id,
        case_name=case_name,
        case_year=case_year,
        jurisdiction=jurisdiction,
        outcome=outcome,
        enforcement_likelihood=enforcement_likelihood,
        confidence_score=confidence_score,
    )
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match


async def get_precedent_match_by_id(
    session: AsyncSession, match_id: UUID
) -> Optional[PrecedentMatch]:
    """Get precedent match by ID."""
    result = await session.execute(
        select(PrecedentMatch).where(PrecedentMatch.id == match_id)
    )
    return result.scalars().first()


async def get_precedent_matches_by_clause_id(
    session: AsyncSession,
    clause_id: UUID,
    limit: int = 10,
) -> List[PrecedentMatch]:
    """Get all precedent matches for a clause."""
    result = await session.execute(
        select(PrecedentMatch)
        .where(PrecedentMatch.clause_id == clause_id)
        .order_by(PrecedentMatch.confidence_score.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def delete_precedent_match(session: AsyncSession, match_id: UUID) -> bool:
    """Delete a precedent match."""
    match = await get_precedent_match_by_id(session, match_id)
    if not match:
        return False

    await session.delete(match)
    await session.commit()
    return True
