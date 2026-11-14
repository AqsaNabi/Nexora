import os
import tempfile

from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from repository.policy import create_policy, create_policy_chunks


def upload_policy(
    policy_name,
    description,
    category,
    file_name,
    file_data
):

    file_size = len(file_data)

    # STEP 1: Store policy in PostgreSQL

    result = create_policy(
        policy_name=policy_name,
        description=description,
        category=category,
        file_name=file_name,
        file_data=file_data,
        file_size=file_size
    )

    policy_id = result["policy_id"]

    # STEP 2: Save PDF temporarily for Docling

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_file:

            temp_file.write(file_data)
            temp_path = temp_file.name

        # STEP 3: Extract text using Docling

        converter = DocumentConverter()

        doc = converter.convert(temp_path)

        markdown_text = doc.document.export_to_markdown()

        # STEP 4: Create chunks

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = text_splitter.split_text(markdown_text)

        if not chunks:
            raise ValueError("No text could be extracted from the PDF.")

        # STEP 5: Store chunks and embeddings in ChromaDB

        chunk_count = create_policy_chunks(
            policy_id=policy_id,
            policy_name=policy_name,
            category=category,
            chunks=chunks
        )

        return {
            "policy_id": policy_id,
            "policy_name": policy_name,
            "category": category,
            "chunks_created": chunk_count,
            "message": "Policy uploaded and RAG updated successfully"
        }

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)