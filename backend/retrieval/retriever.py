from ..ingestion.embedder import get_vector_store


def get_retriever(k=5):
    """
    Returns a high-level LangChain retriever object using MMR to balance relevance with data diversity (e.g., getting chunks from both PDFs and CSVs).
    """
    vector_store = get_vector_store()

    #search type = MMR ensure the retriever doesn't just pull 5
    return vector_store.as_retriever(
        search_type = "mmr",
        search_kwargs={
            "k": k,
            "fetch_k": 20, #Initially fetch 20, then pick the 5 diverse
            "lambda_mult": 0.5
        }
    )

def retrieve_chunks(query: str, k: int = 5):
    """
    Returns a list of dicts with content, source, and similarity scores.
    Useful for the Audit Log and Evaluation layers.
    """
    vector_store = get_vector_store()

    results = vector_store.similarity_search_with_score(query, k=k)

    formatted_results = []

    for doc, score in results:
        #Normalize the index based on the doc_type we set in loader.py
        chunk_index = doc.metadata.get("row_index") if doc.metadata.get("doc_type") == "csv_record" else doc.metadata.get("chunk_id")

        formatted_results.append({
            "text": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "chunk_index": chunk_index,
            "score": float(score)
        })
    return formatted_results