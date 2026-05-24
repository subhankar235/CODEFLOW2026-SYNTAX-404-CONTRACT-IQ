"""Analysis Result repository."""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.analysis_result import AnalysisResult

class AnalysisResultRepository:
    """Repository for AnalysisResult."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_contract_id(self, contract_id: UUID) -> Optional[AnalysisResult]:
        """Get analysis result by contract ID."""
        result = await self.session.execute(
            select(AnalysisResult).where(AnalysisResult.contract_id == contract_id)
        )
        return result.scalars().first()
