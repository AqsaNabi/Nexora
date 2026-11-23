
import os

from fastapi import UploadFile
from dotenv import load_dotenv

from unstructured.partition.api import partition_via_api
from unstructured.chunking.title import chunk_by_title

from backend.repository.policy import (
    create_policy,
    create_policy_chunks
)

load_dotenv()

UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY")
UNSTRUCTURED_API_URL = os.getenv("UNSTRUCTURED_API_URL")


async def upload_policy(
    description: str,
    category: str,
    file: UploadFile
):
    # STEP 1: Read uploaded PDF
    file_name = file.filename

    if not file_name or not file_name.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported.")

    file_data = await file.read()

    if not file_data:
        raise ValueError("Uploaded PDF is empty.")

    file_size = len(file_data)

    if not UNSTRUCTURED_API_KEY or not UNSTRUCTURED_API_URL:
        raise ValueError("Unstructured API configuration is missing.")

    # STEP 2: Store original PDF in PostgreSQL
    result = create_policy(
        description=description,
        category=category,
        file_name=file_name,
        file_data=file_data,
        file_size=file_size
    )

    policy_id = result["policy_id"]

    # STEP 3: Extract PDF content using Unstructured API
    elements = partition_via_api(
        file=file_data,
        metadata_filename=file_name,
        api_key=UNSTRUCTURED_API_KEY,
        api_url=UNSTRUCTURED_API_URL,
        content_type="application/pdf",
        strategy="hi_res",
        coordinates=True,
        pdf_infer_table_structure=True
    )

    if not elements:
        raise ValueError("No content extracted from PDF.")

    # STEP 4: Create chunks
    chunks = chunk_by_title(
        elements,
        max_characters=1000,
        new_after_n_chars=800,
        combine_text_under_n_chars=200,
        include_orig_elements=True
    )

    if not chunks:
        raise ValueError("No chunks generated.")

    # STEP 5: Prepare chunk text and metadata
    processed_chunks = []

    for index, chunk in enumerate(chunks):

        if not chunk.text or not chunk.text.strip():
            continue

        original_elements = (
            getattr(chunk.metadata, "orig_elements", None) or []
        )

        coordinates = []
        page_numbers = []
        element_types = []

        for element in original_elements:

            element_metadata = element.metadata

            # Extract page number
            page_number = getattr(
                element_metadata,
                "page_number",
                None
            )

            if page_number is not None:
                page_numbers.append(page_number)

            # Extract element type
            element_type = getattr(
                element,
                "category",
                None
            )

            if element_type and element_type not in element_types:
                element_types.append(element_type)

            # Extract coordinates
            coords = getattr(
                element_metadata,
                "coordinates",
                None
            )

            if coords:

                points = [
                    [float(point[0]), float(point[1])]
                    for point in coords.points
                ]

                system = coords.system

                system_info = {
                    "width": getattr(system, "width", None),
                    "height": getattr(system, "height", None),
                    "name": getattr(system, "name", str(system))
                }

                coordinates.append({
                    "page_number": page_number,
                    "element_type": element_type,
                    "points": points,
                    "system": system_info
                })

        # Remove duplicate page numbers
        page_numbers = list(dict.fromkeys(page_numbers))

        processed_chunks.append({
            "chunk_index": index,
            "text": chunk.text,
            "metadata": {
                "policy_id": policy_id,
                "category": category,
                "page_number": page_numbers,
                "element_type": element_types,
                "coordinates": coordinates
            }
        })

    if not processed_chunks:
        raise ValueError("No valid chunks generated.")

    # STEP 6: Generate embeddings and store chunks in PostgreSQL
    chunk_count = create_policy_chunks(
        policy_id=policy_id,
        category=category,
        chunks=processed_chunks
    )

    # STEP 7: Return response
    return {
        "policy_id": policy_id,
        "category": category,
        "file_name": file_name,
        "file_size": file_size,
        "chunks_created": chunk_count,
        "message": "Policy stored and RAG updated successfully"
    }
