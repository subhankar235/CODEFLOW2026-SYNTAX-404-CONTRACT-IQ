"""
Chat service — orchestration logic for Q&A chat.
Formats conversation history and calls the chat pipeline.
"""

import logging
from typing import List, Dict, Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID

from app.repositories import contract_repo
from app.models.contract import Contract

logger = logging.getLogger(__name__)


async def verify_contract_and_get_id(
    db: AsyncSession,
    contract_id_str: str,
    user_id: str,
) -> UUID | None:
    """
    Verify contract exists and belongs to user.
    Returns contract_id UUID if valid, None otherwise.
    """
    try:
        contract_id = UUID(contract_id_str)
    except ValueError:
        return None

    from sqlalchemy import select
    from app.models.user import User
    
    user_result = await db.execute(select(User).where(User.clerk_user_id == user_id))
    db_user = user_result.scalars().first()
    
    if not db_user:
        return None

    contract = await contract_repo.get_contract_by_id(db, contract_id, db_user.id)

    if not contract:
        return None

    return contract_id


async def check_embeddings_exist(
    db: AsyncSession,
    contract_id: UUID,
) -> bool:
    """
    Check if embeddings exist for this contract using the async session.
    """
    try:
        result = await db.execute(
            text(
                """SELECT COUNT(*) FROM embeddings 
                   WHERE contract_id = :contract_id"""
            ),
            {"contract_id": str(contract_id)},
        )
        count = result.scalar_one()
        return count > 0
    except Exception as e:
        # Table might not exist or embeddings not set up — allow anyway
        logger.warning("Could not check embeddings (table may not exist): %s", e)
        return True  # Allow chat even without embeddings check


def format_conversation_history(
    history: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Format conversation history for the chat pipeline.
    """
    if not history:
        return []

    formatted = []
    for msg in history:
        if "role" in msg and "content" in msg:
            formatted.append({"role": msg["role"], "content": msg["content"]})
    return formatted


async def stream_chat_response(
    contract_id: str,
    question: str,
    conversation_history: List[Dict[str, str]] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream chat response using the AI chat pipeline.
    Yields SSE-formatted events: data: {json}\n\n
    """
    logger.info("Streaming chat response for contract %s", contract_id)

    try:
        import sys
        import os
        
        # Add the root directory to sys.path so we can import services.ai from services/api
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, "../../../../"))
        if root_dir not in sys.path:
            sys.path.append(root_dir)

        from services.ai.app.rag.chat_pipeline import answer_question

        history = format_conversation_history(conversation_history or [])

        async for event in answer_question(contract_id, question, history):
            yield event

    except ImportError as e:
        # AI service not available — yield a graceful fallback response
        logger.warning(f"AI service not available, using fallback response: {e}")
        fallback = (
            "The AI analysis service is currently unavailable. "
            "Please ensure the AI service is running and try again."
        )
        import json
        for chunk in fallback.split(" "):
            yield f"data: {json.dumps({'type': 'token', 'content': chunk + ' '})}\n\n"

    except Exception as e:
        logger.error("Chat streaming error: %s", e)
        import json
        error_msg = f"I encountered an error while processing your question: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
