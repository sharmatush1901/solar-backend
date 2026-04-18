from fastapi import APIRouter, UploadFile, File
import shutil
import os

from app.services.rag_service import create_vector_store

router = APIRouter()

UPLOAD_PATH = "app/data/docs"

@router.post("/pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Ensure folder exists
        os.makedirs(UPLOAD_PATH, exist_ok=True)

        file_path = os.path.join(UPLOAD_PATH, file.filename)

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Rebuild vector store
        create_vector_store()

        return {"message": f"{file.filename} uploaded and processed successfully ✅"}

    except Exception as e:
        return {"error": str(e)}