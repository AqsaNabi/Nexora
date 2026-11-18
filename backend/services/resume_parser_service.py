
from io import BytesIO

import fitz
from docx import Document


def extract_pdf_text(resume_content):
    """Extract text from a PDF resume."""

    try:
        pdf_document = fitz.open(
            stream=resume_content,
            filetype="pdf"
        )

        extracted_text = []

        for page in pdf_document:
            extracted_text.append(
                page.get_text("text")
            )

        pdf_document.close()

        return "\n".join(extracted_text).strip()

    except Exception as error:
        raise ValueError(
            f"Failed to extract PDF text: {error}"
        )


def extract_docx_text(resume_content):
    """Extract text from a DOCX resume."""

    try:
        document = Document(
            BytesIO(resume_content)
        )

        extracted_text = []

        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                extracted_text.append(paragraph.text)

        # Extract text from tables as well.
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        extracted_text.append(cell.text)

        return "\n".join(extracted_text).strip()

    except Exception as error:
        raise ValueError(
            f"Failed to extract DOCX text: {error}"
        )


def extract_resume_text(
    resume_content,
    resume_filename,
    resume_content_type
):
    """Extract text from supported resume formats."""

    if resume_content_type == "application/pdf":
        text = extract_pdf_text(resume_content)

    elif resume_content_type == (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ):
        text = extract_docx_text(resume_content)

    else:
        raise ValueError(
            f"Unsupported resume format: {resume_content_type}"
        )

    if not text:
        raise ValueError(
            f"No readable text found in {resume_filename}. "
            "The resume may be scanned or image-based."
        )

    return text
