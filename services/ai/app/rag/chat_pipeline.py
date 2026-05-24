"""
Q&A Chat Pipeline (STEP 8.2).
Uses LangChain with pgvector retriever for contract Q&A.
Streams answers as SSE events with clause citations.
"""

import os
import json
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
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

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("FAST_MODEL", "google/gemini-2.0-flash-001")

    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base=OPENROUTER_BASE_URL,
        streaming=streaming,
        temperature=0.7,
    )


def _build_prompt():
    """Build the chat prompt template."""
    from langchain.prompts import PromptTemplate

    prompt_template = """You are a contract analysis assistant. You help users understand their contracts from their perspective as the employee/service provider.

RULES:
1. Always cite the specific clause or section you reference (e.g., "Section 4.2 states..." or "The non-compete clause says...")
2. If the answer is NOT in the provided context, say "This topic is not addressed in the contract" - never fabricate contract terms.
3. Be concise and accurate. Use plain language.
4. If you reference a specific clause, include the clause text in your answer.
5. Highlight risks clearly and explain their practical implications.

Context from contract:
{context}

Conversation History:
{history}

Question: {question}

Answer:"""

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
        from langchain.schema import HumanMessage
        
        streaming_model = _get_chat_model(streaming=True)
        accumulated = ""
        
        async for chunk in streaming_model.astream([HumanMessage(content=formatted_prompt)]):
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
