"""Counter-offer repository — database query functions for counter-offers."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.counter_offer import CounterOffer


async def create_counter_offer(
    session: AsyncSession,
    clause_id: UUID,
    aggressive_version: str,
    balanced_version: str,
    conservative_version: str,
    negotiation_email: str,
) -> CounterOffer:
    """Create a new counter-offer."""
    offer = CounterOffer(
        clause_id=clause_id,
        aggressive_version=aggressive_version,
        balanced_version=balanced_version,
        conservative_version=conservative_version,
        negotiation_email=negotiation_email,
    )
    session.add(offer)
    await session.commit()
    await session.refresh(offer)
    return offer


async def get_counter_offer_by_id(
    session: AsyncSession, offer_id: UUID
) -> Optional[CounterOffer]:
    """Get counter-offer by ID."""
    result = await session.execute(
        select(CounterOffer).where(CounterOffer.id == offer_id)
    )
    return result.scalars().first()


async def get_counter_offers_by_clause_id(
    session: AsyncSession,
    clause_id: UUID,
) -> List[CounterOffer]:
    """Get all counter-offers for a clause."""
    result = await session.execute(
        select(CounterOffer).where(CounterOffer.clause_id == clause_id)
    )
    return result.scalars().all()


async def delete_counter_offer(session: AsyncSession, offer_id: UUID) -> bool:
    """Delete a counter-offer."""
    offer = await get_counter_offer_by_id(session, offer_id)
    if not offer:
        return False

    await session.delete(offer)
    await session.commit()
    return True
