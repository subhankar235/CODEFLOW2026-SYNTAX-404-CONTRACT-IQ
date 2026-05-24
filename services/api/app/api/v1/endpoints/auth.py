from fastapi import APIRouter, Request, HTTPException, Depends, status
from svix.webhooks import Webhook, WebhookVerificationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_async_session
from app.repositories import user_repo
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/clerk")
async def clerk_webhook(
    request: Request, db: AsyncSession = Depends(get_async_session)
):
    """Handle Clerk webhooks for user sync."""
    if not settings.clerk_webhook_secret:
        logger.error("CLERK_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    # Get headers
    headers = request.headers
    svix_id = headers.get("svix-id")
    svix_timestamp = headers.get("svix-timestamp")
    svix_signature = headers.get("svix-signature")

    if not svix_id or not svix_timestamp or not svix_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing svix headers"
        )

    # Get body
    body = await request.body()
    payload = body.decode("utf-8")

    # Verify signature
    wh = Webhook(settings.clerk_webhook_secret)
    try:
        msg = wh.verify(payload, headers)
    except WebhookVerificationError as e:
        logger.warning(f"Webhook verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature"
        )

    # Handle events
    event_type = msg.get("type")
    data = msg.get("data", {})

    if event_type in ["user.created", "user.updated"]:
        clerk_user_id = data.get("id")
        email_addresses = data.get("email_addresses", [])
        primary_email = ""
        for email in email_addresses:
            if email.get("id") == data.get("primary_email_address_id"):
                primary_email = email.get("email_address")
                break

        if not primary_email and email_addresses:
            primary_email = email_addresses[0].get("email_address")

        if clerk_user_id and primary_email:
            await user_repo.upsert_user(
                db, clerk_user_id=clerk_user_id, email=primary_email
            )
            logger.info(f"User {clerk_user_id} synced via webhook ({event_type})")
        else:
            logger.warning(
                f"Incomplete user data in webhook: {clerk_user_id}, {primary_email}"
            )

    return {"status": "ok"}
