import os
import uuid
import shutil
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from app.core.config import settings

chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)

embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

COLLECTION_NAME = "aria_knowledge_base"

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


def get_collection():
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_document(file_path: str, filename: str, doc_id: str) -> int:
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in {".txt", ".md"}:
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    collection = get_collection()
    collection.add(
        documents=[c.page_content for c in chunks],
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
        metadatas=[
            {
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": i,
                "page": str(c.metadata.get("page", 0)),
            }
            for i, c in enumerate(chunks)
        ],
    )

    return len(chunks)


def save_and_ingest(file_content: bytes, filename: str) -> dict:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")

    with open(file_path, "wb") as f:
        f.write(file_content)

    try:
        chunk_count = ingest_document(file_path, filename, doc_id)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return {"id": doc_id, "filename": filename, "chunks": chunk_count}


def delete_document(doc_id: str):
    collection = get_collection()
    results = collection.get(where={"doc_id": doc_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def list_documents() -> list[dict]:
    collection = get_collection()
    results = collection.get()
    seen = {}
    for meta in results["metadatas"]:
        did = meta["doc_id"]
        if did not in seen:
            seen[did] = {"id": did, "filename": meta["filename"]}
    return list(seen.values())
