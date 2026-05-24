from fastapi import APIRouter, Depends
from app.api.v1.endpoints import (
    auth,
    contracts,
    upload,
    analysis,
    streaming,
    counter_offer,
    summary,
    power,
    precedent,
    report,
    chat,
    translate,
    health,
    dashboard,
    blockchain,
)
from app.core.security import get_current_user_id

api_router = APIRouter()

# Public routes - mounted directly on /api/v1
api_router.include_router(health.router, tags=["health"])
api_router.include_router(
    auth.router, prefix="/webhooks", tags=["auth"]
)  # Contains webhooks, which verify their own signatures

# Protected routes
protected_dependency = [Depends(get_current_user_id)]

api_router.include_router(
    contracts.router,
    prefix="/contracts",
    tags=["contracts"],
    dependencies=protected_dependency,
)

api_router.include_router(
    upload.router, prefix="/upload", tags=["upload"], dependencies=protected_dependency
)

api_router.include_router(
    analysis.router,
    prefix="/scan",
    tags=["analysis"],
    dependencies=protected_dependency,
)

api_router.include_router(
    streaming.router,
    tags=["streaming"],  # prefix is handled in endpoints (e.g. /scan/{jobId}/stream)
    # No dependencies — EventSource cannot send Authorization headers;
    # the endpoint validates auth via the ?token= query parameter internally.
)

api_router.include_router(
    counter_offer.router,
    prefix="/counter-offer",
    tags=["counter-offer"],
    dependencies=protected_dependency,
)

api_router.include_router(
    summary.router,
    prefix="/summary",
    tags=["summary"],
    dependencies=protected_dependency,
)

api_router.include_router(
    power.router, prefix="/power", tags=["power"], dependencies=protected_dependency
)

api_router.include_router(
    precedent.router,
    prefix="/precedent",
    tags=["precedent"],
    dependencies=protected_dependency,
)

api_router.include_router(
    report.router, prefix="/report", tags=["report"], dependencies=protected_dependency
)

api_router.include_router(
    chat.router, prefix="/chat", tags=["chat"], dependencies=protected_dependency
)

api_router.include_router(
    translate.router,
    prefix="/translate",
    tags=["translate"],
    dependencies=protected_dependency,
)

api_router.include_router(
    dashboard.router, prefix="/dashboard", tags=["dashboard"], dependencies=protected_dependency
)

api_router.include_router(
    blockchain.router, prefix="/blockchain", tags=["blockchain"], dependencies=protected_dependency
)
