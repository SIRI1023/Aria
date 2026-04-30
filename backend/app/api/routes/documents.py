from fastapi import APIRouter, UploadFile, File, HTTPException
from app.rag.ingest import save_and_ingest, delete_document, list_documents

router = APIRouter()


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    try:
        result = save_and_ingest(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
    return result


@router.get("/documents")
async def get_documents():
    return list_documents()


@router.delete("/documents/{doc_id}")
async def remove_document(doc_id: str):
    delete_document(doc_id)
    return {"status": "deleted"}
