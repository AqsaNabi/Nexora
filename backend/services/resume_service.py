
import uuid
from pathlib import Path

from fastapi import UploadFile


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

RESUME_DIRECTORY = BASE_DIR / "uploads" / "resumes"

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx"
}


# ============================================================
# UPLOAD RESUME
# ============================================================

async def save_resume(file: UploadFile):

    if not file or not file.filename:
        raise ValueError("Please select a resume file.")

    original_filename = Path(file.filename).name

    extension = Path(original_filename).suffix.lower()

    # Validate extension.
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only PDF and DOCX resume files are allowed."
        )

    # Read file content.
    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise ValueError("The uploaded file is empty.")

    # Validate file size.
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(
            "Resume size cannot exceed 5 MB."
        )

    # Validate actual file signature.
    if extension == ".pdf":

        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file.")

    elif extension == ".docx":

        if not content.startswith(b"PK"):
            raise ValueError("Invalid DOCX file.")

    # Generate a unique filename.
    resume_id = str(uuid.uuid4())

    saved_filename = f"{resume_id}{extension}"

    # Create storage directory if it doesn't exist.
    RESUME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = RESUME_DIRECTORY / saved_filename

    try:

        file_path.write_bytes(content)

    except OSError as error:

        raise RuntimeError(
            f"Could not save resume: {error}"
        )

    finally:

        await file.close()

    return {
        "resume_id": resume_id,
        "original_filename": original_filename,
        "saved_filename": saved_filename,
        "file_extension": extension,
        "file_size": len(content),
        "storage_status": "saved"
    }
