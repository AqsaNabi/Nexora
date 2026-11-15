
from pathlib import Path

from backend.repository.recruitment_repository import (
    attach_resume_to_applicant
)

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


async def save_resume(
    file,
    post_id: str,
    email: str
):
    if not file or not file.filename:
        raise ValueError("Please select a resume file.")

    if not post_id or not email:
        raise ValueError("Recruitment post ID and email are required.")

    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF and DOCX resume files are allowed.")

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise ValueError("The uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("Resume size cannot exceed 5 MB.")

    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file.")

        content_type = "application/pdf"

    else:
        if not content.startswith(b"PK"):
            raise ValueError("Invalid DOCX file.")

        content_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    try:
        result = attach_resume_to_applicant(
            post_id=post_id.strip(),
            email=email.strip(),
            resume_content=content,
            resume_filename=original_filename,
            resume_content_type=content_type
        )

        return result

    finally:
        await file.close()
