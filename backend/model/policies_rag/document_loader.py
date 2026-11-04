
import fitz #	PyMuPDF library, used to read PDF files.
from pathlib import Path

from .config import POLICY_FILE


def load_policy_document(file_path: Path = POLICY_FILE):
    """
    Load a PDF policy document and extract text page by page.

    Args:
        file_path (Path): Location of the company policy PDF.

    Returns:
        list: A list of dictionaries containing page numbers and extracted text.
    """

    # Check whether the PDF exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Policy document not found at: {file_path}"
        )

    # Store extracted page information
    pages = []

    # Open the PDF document
    with fitz.open(file_path) as pdf_document:

        # Check whether the PDF contains pages
        if len(pdf_document) == 0:
            raise ValueError("The policy PDF is empty.")

        # Extract text from each page
        for page_number, page in enumerate(pdf_document, start=1):

            extracted_text = page.get_text("text")

            # Store only pages containing text
            if extracted_text.strip():

                pages.append({
                    "page_number": page_number,
                    "text": extracted_text
                })

    if not pages:
        raise ValueError(
            "No extractable text found in the PDF. "
            "The document may require OCR."
        )

    return pages


if __name__ == "__main__":

    try:
        extracted_pages = load_policy_document()

        print(f"Successfully loaded {len(extracted_pages)} pages.")

        for page in extracted_pages:
            print(f"\n--- Page {page['page_number']} ---")
            print(page["text"][:500])

    except Exception as error:
        print(f"Error loading policy document: {error}")
