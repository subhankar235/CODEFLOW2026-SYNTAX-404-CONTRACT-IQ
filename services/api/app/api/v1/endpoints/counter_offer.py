"""
<<<<<<< HEAD
Counter-Offer Endpoints — POST/GET /api/v1/counter-offer/{clauseId}
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import httpx
import os

from app.api.deps import get_current_user, get_db
from app.repositories import user_repo
from app.models.user import User
from app.models.clause import Clause
from app.models.contract import Contract
from app.models.counter_offer import CounterOffer
from sqlalchemy import select

from app.core.celery import celery_app

router = APIRouter()
logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")


def verify_user_and_get_internal_id(db: AsyncSession, clerk_user_id: str):
    """Convert Clerk user_id to internal UUID."""
    from uuid import UUID
    try:
        return UUID(clerk_user_id)
    except ValueError:
        return None


@router.post("/{clause_id}")
async def generate_counter_offer(
    clause_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers counter-offer generation for a HIGH-risk clause.
    For demo clause IDs, calls the AI service directly.
    """
    if clause_id.startswith("clause-"):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{AI_SERVICE_URL}/api/v1/counter-offer",
                    json={
                        "clause_text": "The Employee agrees that during the term of employment and for a period of two (2) years following termination, the Employee shall not engage in any business that competes directly or indirectly with the Employer within a radius of fifty (50) miles of any of the Employer's offices.",
                        "clause_type": "employment",
                        "contract_type": "employment",
                        "user_role": "employee",
                        "risk_category": clause_id.replace("clause-", "clause_"),
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "ready",
                            "clause_id": clause_id,
                            "aggressive_clause": data.get("aggressive_clause", ""),
                            "explanation_aggressive": data.get("explanation_aggressive", ""),
                            "balanced_clause": data.get("balanced_clause", ""),
                            "explanation_balanced": data.get("explanation_balanced", ""),
                            "conservative_clause": data.get("conservative_clause", ""),
                            "explanation_conservative": data.get("explanation_conservative", ""),
                            "negotiation_email": data.get("negotiation_email", ""),
                        },
                    )
        except Exception as e:
            logger.warning("AI service call failed for counter-offer demo: %s", e)
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "clause_id": clause_id},
        )

    try:
        clause_uuid = UUID(clause_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clause ID"
        )

    # Attempt to fetch user by Clerk ID; if that fails, fall back to internal UUID lookup
    user = await user_repo.get_user_by_clerk_id(db, current_user)
    if not user:
        # current_user might already be an internal UUID string
        try:
            from uuid import UUID as _UUID
            internal_id = _UUID(current_user)
            user = await user_repo.get_user_by_id(db, internal_id)
        except Exception:
            user = None
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where((Clause.id == clause_uuid) & (Contract.user_id == user.id))
    )
    clause = result.scalars().first()

    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clause not found or access denied",
        )

    result = await db.execute(
        select(CounterOffer).where(CounterOffer.clause_id == clause_uuid)
    )
    existing = result.scalars().first()

    if existing:
        return JSONResponse(
            status_code=200,
            content={
                "clause_id": str(existing.clause_id),
                "aggressive_clause": existing.aggressive_version,
                "explanation_aggressive": "This aggressive version provides maximum protection by significantly limiting the restriction or maximizing the obligation in your favor.",
                "balanced_clause": existing.balanced_version,
                "explanation_balanced": "This compromise version balances key interests of both parties to ensure mutual fairness and a higher likelihood of acceptance.",
                "conservative_clause": existing.conservative_version,
                "explanation_conservative": "This conservative version introduces minor changes to slightly improve your position while maintaining standard terms.",
                "negotiation_email": existing.negotiation_email,
            },
        )

    try:
        task = celery_app.send_task(
            "generate_counter_offer",
            args=[clause_id],
        )
        logger.info("Queued counter-offer task %s for clause %s", task.id, clause_id)
    except Exception as e:
        logger.error("Failed to queue counter-offer task: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue counter-offer generation",
        )

    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "task_id": task.id,
            "clause_id": clause_id,
        },
    )


@router.get("/{clause_id}")
async def get_counter_offer(
    clause_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Polls for counter-offer result.
    """
    if clause_id.startswith("clause-"):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{AI_SERVICE_URL}/api/v1/counter-offer",
                    json={
                        "clause_text": "The Employee agrees that during the term of employment and for a period of two (2) years following termination, the Employee shall not engage in any business that competes directly or indirectly with the Employer within a radius of fifty (50) miles of any of the Employer's offices.",
                        "clause_type": "employment",
                        "contract_type": "employment",
                        "user_role": "employee",
                        "risk_category": clause_id.replace("clause-", "clause_"),
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "ready",
                            "clause_id": clause_id,
                            "aggressive_clause": data.get("aggressive_clause", ""),
                            "explanation_aggressive": data.get("explanation_aggressive", ""),
                            "balanced_clause": data.get("balanced_clause", ""),
                            "explanation_balanced": data.get("explanation_balanced", ""),
                            "conservative_clause": data.get("conservative_clause", ""),
                            "explanation_conservative": data.get("explanation_conservative", ""),
                            "negotiation_email": data.get("negotiation_email", ""),
                        },
                    )
        except Exception as e:
            logger.warning("AI service call failed for counter-offer GET demo: %s", e)
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "clause_id": clause_id},
        )

    try:
        clause_uuid = UUID(clause_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clause ID"
        )

    user = await user_repo.get_user_by_clerk_id(db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where((Clause.id == clause_uuid) & (Contract.user_id == user.id))
    )
    clause = result.scalars().first()

    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clause not found or access denied",
        )

    result = await db.execute(
        select(CounterOffer).where(CounterOffer.clause_id == clause_uuid)
    )
    counter_offer = result.scalars().first()

    if not counter_offer:
        return JSONResponse(
            status_code=202,
            content={"status": "processing"},
        )

    return JSONResponse(
        status_code=200,
        content={
            "clause_id": str(counter_offer.clause_id),
            "aggressive_clause": counter_offer.aggressive_version,
            "explanation_aggressive": "This aggressive version provides maximum protection by significantly limiting the restriction or maximizing the obligation in your favor.",
            "balanced_clause": counter_offer.balanced_version,
            "explanation_balanced": "This compromise version balances key interests of both parties to ensure mutual fairness and a higher likelihood of acceptance.",
            "conservative_clause": counter_offer.conservative_version,
            "explanation_conservative": "This conservative version introduces minor changes to slightly improve your position while maintaining standard terms.",
            "negotiation_email": counter_offer.negotiation_email,
        },
    )
=======
Q&A Chat Pipeline (STEP 8.2).
Uses LangChain with pgvector retriever for contract Q&A.
Streams answers as SSE events with clause citations.
"""

import os
import json
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from dotenv import load_dotenv, find_dotenv

# Find .env by walking up from this file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
root_env_path = os.path.join(current_dir, "../../../../.env")
load_dotenv(dotenv_path=os.path.abspath(root_env_path))

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "contract_qa"


def _make_token_event(content: str) -> str:
    """Create a SSE token event string."""
    return f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"


def _make_citation_event(clause_id: str) -> str:
    """Create a SSE citation event string."""
    return f"data: {json.dumps({'type': 'citation', 'clause_id': clause_id})}\n\n"


def _make_error_event(message: str) -> str:
    """Create a SSE error event string."""
    return f"data: {json.dumps({'type': 'error', 'content': message})}\n\n"


def _get_vectorstore(contract_id: str):
    """
    Get PGVector vectorstore scoped to a specific contract_id.
    """
    from langchain_community.vectorstores import PGVector
    from langchain_community.embeddings import SentenceTransformerEmbeddings

    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)

    connection_string = os.environ.get("DATABASE_URL", "")
    # Convert asyncpg URL to standard postgresql for LangChain
    if "postgresql+asyncpg" in connection_string:
        connection_string = connection_string.replace(
            "postgresql+asyncpg", "postgresql"
        )

    return PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=connection_string,
        embedding_function=embeddings,
        use_jsonb=True,
    )


def _get_chat_model(streaming: bool = False):
    """
    Get LLM for chat. Uses OpenRouter via OpenAI-compatible API.
    """
    from langchain_community.chat_models import ChatOpenAI

    api_key = os.environ.get("GROQ_API_KEY", "")
    model = os.environ.get("FAST_MODEL", "llama-3.1-8b-instant")

    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base=GROQ_BASE_URL,
        streaming=streaming,
        temperature=0.7,
    )


def _build_prompt():
    """Build the chat prompt template."""
    from langchain.prompts import PromptTemplate

    prompt_template = """You are a friendly, conversational legal assistant. Your goal is to help the user understand their contract in simple, plain language.

RULES:
1. Be Conversational: Respond naturally and warmly to greetings (e.g., "Hi", "Hello"). If the user is just saying hello, DO NOT mention the contract, DO NOT mention missing clauses, and DO NOT mention previous conversations. Just say hello back and ask how you can help them with their contract!
2. Cite Clauses: When answering a specific question about the contract, always cite the specific clause or section. Include a brief snippet of the clause text if helpful.
3. Stick to Context: If the user asks a specific question about their contract terms, and the answer is NOT in the provided context, politely explain that you cannot find that specific term. NEVER fabricate terms or guess.
4. Explain Risks: Highlight any risks clearly and explain their practical implications like you are talking to a friend. Avoid overly robotic or generic phrasing.
5. Empathy: The user is likely an employee or service provider. Frame your answers to protect their interests and help them understand what they are signing.

Context from contract:
{context}

Conversation History:
{history}

User: {question}

Assistant:"""

    return PromptTemplate(
        template=prompt_template,
        input_variables=["context", "history", "question"]
    )


async def answer_question(
    contract_id: str,
    question: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> AsyncGenerator[str, None]:
    """
    Answer a question about a contract using RAG.
    Yields SSE event strings.
    """
    logger.info("Processing question for contract %s: %s", contract_id, question[:100])

    try:
        from langchain.chains import RetrievalQA

        vectorstore = _get_vectorstore(contract_id)

        search_kwargs = {
            "k": 5,
            "filter": {"contract_id": contract_id},
        }
        retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

        chat_model = _get_chat_model(streaming=False)

        # Build conversation history string
        history_str = ""
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 3 exchanges
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_str += f"{role}: {msg.get('content', '')}\n"

        # Retrieve relevant docs
        docs = retriever.get_relevant_documents(question)
        context = "\n\n---\n\n".join([doc.page_content for doc in docs])

        if not context:
            context = "No specific clauses found for this query."

        # Build the prompt manually
        prompt = _build_prompt()
        formatted_prompt = prompt.format(
            context=context,
            history=history_str or "No previous conversation.",
            question=question,
        )

        # Stream the response token by token
        from langchain.schema import HumanMessage, SystemMessage
        
        streaming_model = _get_chat_model(streaming=True)
        accumulated = ""
        
        system_instruction = (
            "You are a friendly, helpful legal assistant. Your tone is warm, professional, and conversational. "
            "If the user asks a question about their contract, answer it using the provided context. "
            "If the user is just saying hello, greet them back warmly and ask how you can help. "
            "Do NOT fabricate information."
        )

        async for chunk in streaming_model.astream([
            SystemMessage(content=system_instruction),
            HumanMessage(content=formatted_prompt)
        ]):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                accumulated += token
                yield _make_token_event(token)

        # Extract clause citation from source documents
        clause_id = None
        for doc in docs:
            metadata = doc.metadata or {}
            # Try multiple possible metadata key names
            cid = (
                metadata.get("clause_id")
                or metadata.get("id")
                or metadata.get("chunk_id")
            )
            if cid:
                clause_id = str(cid)
                break

        if clause_id:
            yield _make_citation_event(clause_id)

    except Exception as e:
        logger.error("Chat pipeline error: %s", e, exc_info=True)
        error_msg = f"I encountered an error while processing your question. Please try again."
        yield _make_error_event(error_msg)
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
