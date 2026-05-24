"""
Q&A Chat Pipeline (STEP 8.2).
Uses LangChain with pgvector retriever for contract Q&A.
Streams answers as SSE events with clause citations.
"""

import os
import json
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
<<<<<<< HEAD

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
=======
from dotenv import load_dotenv, find_dotenv

# Find .env by walking up from this file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
root_env_path = os.path.join(current_dir, "../../../../.env")
load_dotenv(dotenv_path=os.path.abspath(root_env_path))

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
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

<<<<<<< HEAD
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("FAST_MODEL", "google/gemini-2.0-flash-001")
=======
    api_key = os.environ.get("GROQ_API_KEY", "")
    model = os.environ.get("FAST_MODEL", "llama-3.1-8b-instant")
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa

    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
<<<<<<< HEAD
        openai_api_base=OPENROUTER_BASE_URL,
=======
        openai_api_base=GROQ_BASE_URL,
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
        streaming=streaming,
        temperature=0.7,
    )


def _build_prompt():
    """Build the chat prompt template."""
    from langchain.prompts import PromptTemplate

<<<<<<< HEAD
    prompt_template = """You are a contract analysis assistant. You help users understand their contracts from their perspective as the employee/service provider.

RULES:
1. Always cite the specific clause or section you reference (e.g., "Section 4.2 states..." or "The non-compete clause says...")
2. If the answer is NOT in the provided context, say "This topic is not addressed in the contract" - never fabricate contract terms.
3. Be concise and accurate. Use plain language.
4. If you reference a specific clause, include the clause text in your answer.
5. Highlight risks clearly and explain their practical implications.
=======
    prompt_template = """You are a friendly, conversational legal assistant. Your goal is to help the user understand their contract in simple, plain language.

RULES:
1. Be Conversational: Respond naturally and warmly to greetings (e.g., "Hi", "Hello"). If the user is just saying hello, DO NOT mention the contract, DO NOT mention missing clauses, and DO NOT mention previous conversations. Just say hello back and ask how you can help them with their contract!
2. Cite Clauses: When answering a specific question about the contract, always cite the specific clause or section. Include a brief snippet of the clause text if helpful.
3. Stick to Context: If the user asks a specific question about their contract terms, and the answer is NOT in the provided context, politely explain that you cannot find that specific term. NEVER fabricate terms or guess.
4. Explain Risks: Highlight any risks clearly and explain their practical implications like you are talking to a friend. Avoid overly robotic or generic phrasing.
5. Empathy: The user is likely an employee or service provider. Frame your answers to protect their interests and help them understand what they are signing.
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa

Context from contract:
{context}

Conversation History:
{history}

<<<<<<< HEAD
Question: {question}

Answer:"""
=======
User: {question}

Assistant:"""
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa

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
<<<<<<< HEAD
        from langchain.schema import HumanMessage
=======
        from langchain.schema import HumanMessage, SystemMessage
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
        
        streaming_model = _get_chat_model(streaming=True)
        accumulated = ""
        
<<<<<<< HEAD
        async for chunk in streaming_model.astream([HumanMessage(content=formatted_prompt)]):
=======
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
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
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
