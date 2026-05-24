"""
Dashboard Endpoint — GET /api/v1/dashboard
"""

import logging
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_dashboard():
    """Simple dashboard - no DB queries for now."""
    return {
        "contracts": [],
        "power_trend": None,
    }