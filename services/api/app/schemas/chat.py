"""
Chat (Q&A) schemas — PRD Feature 8.

POST /api/v1/chat/{contractId} streams the answer as SSE.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class ConversationTurn(BaseModel):
    """A single prior exchange in the conversation history."""
    question: str
    answer: str


class ChatRequest(BaseModel):
    """Request body for POST /chat/{contractId}."""
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_history: list[ConversationTurn] = Field(
        default_factory=list,
        description="Prior Q&A turns for follow-up context",
    )


# ---------------------------------------------------------------------------
# Response (non-streaming fallback / citation event)
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    """Non-streaming / final chat response with clause citation."""
    contract_id: UUID
    question: str
    answer: str
    clause_citation: Optional[str] = Field(
        None,
        description="Clause or section reference, e.g. 'Section 4.2'",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Clause IDs or position indices used to generate the answer",
    )
