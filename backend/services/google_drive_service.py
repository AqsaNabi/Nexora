
import re
from io import BytesIO

from backend.services.google_form_service import get_drive_service


MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


def extract_google_drive_file_id(resume_link):
    """Extract Google Drive file ID from a shared URL."""

    if not resume_link:
        raise ValueError("Resume link is missing.")

    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
        r"/document/d/([a-zA-Z0-9_-]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, resume_link)

        if match:
            return match.group(1)

    raise ValueError("Invalid Google Drive resume link.")


def download_resume_from_drive(resume_link):
    """
    Download a PDF or DOCX resume from Google Drive.

    Returns:
        resume_content: bytes
        resume_filename: str
        resume_content_type: str
    """

    file_id = extract_google_drive_file_id(resume_link)

    service = get_drive_service()

    metadata = service.files().get(
        fileId=file_id,
        fields="id,name,mimeType,size"
    ).execute()

    filename = metadata.get("name", "resume")

    mime_type = metadata.get("mimeType")

    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Unsupported resume format: {mime_type}. "
            "Please provide a PDF or DOCX resume."
        )

    file_size = int(metadata.get("size", 0))

    if file_size > MAX_RESUME_SIZE:
        raise ValueError(
            "Resume exceeds the maximum allowed size of 10 MB."
        )

    resume_content = service.files().get_media(
        fileId=file_id
    ).execute()

    if not resume_content:
        raise ValueError("Downloaded resume is empty.")

    if len(resume_content) > MAX_RESUME_SIZE:
        raise ValueError(
            "Downloaded resume exceeds the maximum allowed size."
        )

    return (
        resume_content,
        filename,
        mime_type
    )
