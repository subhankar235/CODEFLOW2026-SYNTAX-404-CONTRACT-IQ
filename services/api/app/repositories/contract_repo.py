"""Contract repository — database query functions for contracts."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.contract import Contract


async def create_contract(
    session: AsyncSession,
    user_id: UUID,
    file_ref: str,
    original_filename: str,
    file_type: str,
    contract_type: Optional[str] = None,
    detected_language: str = "unknown",
    party_roles: Optional[dict] = None,
) -> Contract:
    """Create a new contract."""
    contract = Contract(
        user_id=user_id,
        file_ref=file_ref,
        original_filename=original_filename,
        file_type=file_type,
        contract_type=contract_type,
        detected_language=detected_language,
        party_roles=party_roles,
    )
    session.add(contract)
    await session.commit()
    await session.refresh(contract)
    return contract


async def get_contract_by_id(
    session: AsyncSession, contract_id: UUID, user_id: Optional[UUID] = None
) -> Optional[Contract]:
    """Get contract by ID. If user_id provided, scope to that user for security."""
    query = select(Contract).where(Contract.id == contract_id)
    if user_id:
        query = query.where(Contract.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().first()


async def get_all_contracts_by_user_id(
    session: AsyncSession,
    user_id: UUID,
    limit: int = 100,
    offset: int = 0,
) -> List[Contract]:
    """Get all contracts for a user with analysis results."""
    result = await session.execute(
        select(Contract)
        .options(joinedload(Contract.analysis_result))
        .where(Contract.user_id == user_id)
        .limit(limit)
        .offset(offset)
        .order_by(Contract.created_at.desc())
    )
    return result.scalars().all()


async def update_contract(
    session: AsyncSession,
    contract_id: UUID,
    user_id: UUID,
    **kwargs,
) -> Optional[Contract]:
    """Update contract fields. Scoped to user_id for security."""
    contract = await get_contract_by_id(session, contract_id, user_id)
    if not contract:
        return None

    for key, value in kwargs.items():
        if hasattr(contract, key) and key not in ("id", "user_id", "created_at"):
            setattr(contract, key, value)

    await session.commit()
    await session.refresh(contract)
    return contract


async def delete_contract(
    session: AsyncSession, contract_id: UUID, user_id: UUID
) -> bool:
    """Delete a contract (cascades to clauses, scan_jobs, etc.). Scoped to user_id."""
    contract = await get_contract_by_id(session, contract_id, user_id)
    if not contract:
        return False

    await session.delete(contract)
    await session.commit()
    return True


class ContractRepository:
    """Class-based wrapper for contract repository functions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self, contract_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[Contract]:
        return await get_contract_by_id(self.session, contract_id, user_id)
