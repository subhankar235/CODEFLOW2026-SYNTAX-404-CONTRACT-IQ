from app.rag.embedding_service import generate_embedding
from app.rag.vector_store import collection


def retrieve_relevant_clauses(
    contract_id: str,
    question: str,
    top_k: int = 5
):
    query_embedding = generate_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"contract_id": contract_id}
    )

    documents = results.get("documents", [])

    if not documents or len(documents[0]) == 0:
        return []

    return documents[0]