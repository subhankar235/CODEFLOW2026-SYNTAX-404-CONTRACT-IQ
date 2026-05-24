"""Clause repository — database query functions for clauses."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.clause import Clause


async def create_clause(
    session: AsyncSession,
    contract_id: UUID,
    text: str,
    position_index: int,
    risk_level: str,
    risk_category: Optional[str] = None,
    plain_english: Optional[str] = None,
    worst_case_scenario: Optional[str] = None,
    financial_exposure: Optional[str] = None,
    negotiable: Optional[bool] = None,
    confidence: Optional[float] = None,
    headline: Optional[str] = None,
    scenario: Optional[str] = None,
    probability: Optional[str] = None,
    similar_case: Optional[str] = None,
    requires_attorney_review: bool = False,
) -> Clause:
    """Create a new clause."""
    clause = Clause(
        contract_id=contract_id,
        text=text,
        position_index=position_index,
        risk_level=risk_level,
        risk_category=risk_category,
        plain_english=plain_english,
        worst_case_scenario=worst_case_scenario,
        financial_exposure=financial_exposure,
        negotiable=negotiable,
        confidence=confidence,
        headline=headline,
        scenario=scenario,
        probability=probability,
        similar_case=similar_case,
        requires_attorney_review=requires_attorney_review,
    )
    session.add(clause)
    await session.commit()
    await session.refresh(clause)
    return clause


async def get_clause_by_id(session: AsyncSession, clause_id: UUID) -> Optional[Clause]:
    """Get clause by ID."""
    result = await session.execute(select(Clause).where(Clause.id == clause_id))
    return result.scalars().first()


async def get_all_clauses_by_contract_id(
    session: AsyncSession,
    contract_id: UUID,
    order_by_position: bool = True,
) -> List[Clause]:
    """Get all clauses for a contract."""
    query = select(Clause).where(Clause.contract_id == contract_id)
    if order_by_position:
        query = query.order_by(Clause.position_index.asc())
    result = await session.execute(query)
    return result.scalars().all()


async def bulk_create_clauses(
    session: AsyncSession,
    clauses: List[Clause],
) -> List[Clause]:
    """Bulk create multiple clauses."""
    session.add_all(clauses)
    await session.commit()
    for clause in clauses:
        await session.refresh(clause)
    return clauses


async def update_clause(
    session: AsyncSession,
    clause_id: UUID,
    **kwargs,
) -> Optional[Clause]:
    """Update clause fields."""
    clause = await get_clause_by_id(session, clause_id)
    if not clause:
        return None

    for key, value in kwargs.items():
        if hasattr(clause, key) and key not in (
            "id",
            "contract_id",
            "position_index",
            "created_at",
        ):
            setattr(clause, key, value)

    await session.commit()
    await session.refresh(clause)
    return clause


async def delete_clause(session: AsyncSession, clause_id: UUID) -> bool:
    """Delete a clause."""
    clause = await get_clause_by_id(session, clause_id)
    if not clause:
        return False

    await session.delete(clause)
    await session.commit()
    return True


async def get_by_contract_and_index(
    session: AsyncSession, contract_id: UUID, position_index: int
) -> Optional[Clause]:
    """Get clause by contract_id and position_index."""
    result = await session.execute(
        select(Clause).where(
            Clause.contract_id == contract_id,
            Clause.position_index == position_index,
        )
    )
    return result.scalars().first()


class ClauseRepository:
    """Class-based wrapper for clause repository functions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, clause_id: UUID) -> Optional[Clause]:
        return await get_clause_by_id(self.session, clause_id)

    async def get_by_contract_and_index(
        self, contract_id: UUID, position_index: int
    ) -> Optional[Clause]:
        return await get_by_contract_and_index(
            self.session, contract_id, position_index
        )
