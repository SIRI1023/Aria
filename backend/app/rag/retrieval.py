from app.rag.ingest import get_collection

RELEVANCE_THRESHOLD = 0.3
TOP_K = 3


def retrieve_context(query: str) -> tuple[str, list[dict]]:
    """Search ChromaDB for chunks relevant to the query.
    Returns formatted context string and list of citation dicts."""
    collection = get_collection()

    if collection.count() == 0:
        return "", []

    results = collection.query(
        query_texts=[query],
        n_results=min(TOP_K, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # Cosine distance: 0 = identical, 1 = orthogonal. similarity = 1 - distance
        similarity = 1 - dist
        if similarity >= RELEVANCE_THRESHOLD:
            chunks.append({
                "content": doc,
                "filename": meta["filename"],
                "page": int(meta.get("page", 0)),
                "similarity": round(similarity, 3),
            })

    if not chunks:
        return "", []

    context = "\n\n".join(
        f"[Source {i+1}: {c['filename']}, page {c['page']}]\n{c['content']}"
        for i, c in enumerate(chunks)
    )
    citations = [{"filename": c["filename"], "page": c["page"]} for c in chunks]

    return context, citations
