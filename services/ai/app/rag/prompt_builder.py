from app.rag.embedding_service import generate_embedding
from app.rag.vector_store import collection


def store_clauses(contract_id: str, clauses: list[str]):
    for idx, clause in enumerate(clauses):
        embedding = generate_embedding(clause)

        collection.add(
            ids=[f"{contract_id}_{idx}"],
            documents=[clause],
            embeddings=[embedding],
            metadatas=[{
                "contract_id": contract_id,
                "clause_index": idx
            }]
        )