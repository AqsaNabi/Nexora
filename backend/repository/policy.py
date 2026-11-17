
from database.concect import conn, cur
from psycopg2 import Binary
from psycopg2.extras import Json
from pgvector.psycopg2 import register_vector

from model.policy_embed import embedding_model


# Register pgvector
register_vector(conn)


def create_policy(
    description,
    category,
    file_name,
    file_data,
    file_size
):
    """
    Store every uploaded policy as a new record.
    """

    try:
        cur.execute(
            """
            INSERT INTO policies (
                description,
                category,
                file_name,
                file_data,
                file_size,
                uploaded_at
            )
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING policy_id
            """,
            (
                description,
                category,
                file_name,
                Binary(file_data),
                file_size
            )
        )

        policy_id = cur.fetchone()["policy_id"]

        conn.commit()

        return {
            "policy_id": policy_id,
            "category": category,
            "file_name": file_name,
            "file_size": file_size,
            "message": "New policy uploaded successfully"
        }

    except Exception as e:
        conn.rollback()
        raise e


def get_policy_file(policy_id):
    """
    Fetch the uploaded PDF from PostgreSQL.
    """

    cur.execute(
        """
        SELECT file_name, file_data
        FROM policies
        WHERE policy_id = %s
        """,
        (policy_id,)
    )

    result = cur.fetchone()

    if not result:
        raise ValueError("Policy file not found.")

    return {
        "file_name": result["file_name"],
        "file_data": bytes(result["file_data"])
    }


def create_policy_chunks(
    policy_id,
    category,
    chunks
):
    """
    Generate embeddings and store new chunks.
    """

    if not chunks:
        raise ValueError("No chunks available to store.")

    try:

        # STEP 1: Keep valid chunks
        valid_chunks = [
            chunk
            for chunk in chunks
            if chunk.get("text") and chunk["text"].strip()
        ]

        if not valid_chunks:
            raise ValueError("No valid chunk text found.")

        # STEP 2: Generate embeddings from text only
        chunk_texts = [
            chunk["text"]
            for chunk in valid_chunks
        ]

        embeddings = embedding_model.embed_documents(chunk_texts)

        if len(embeddings) != len(valid_chunks):
            raise ValueError(
                "Number of embeddings does not match number of chunks."
            )

        # STEP 3: Prepare records
        records = []

        for index, (chunk, embedding) in enumerate(
            zip(valid_chunks, embeddings)
        ):

            chunk_index = chunk.get("chunk_index", index)

            metadata = dict(chunk.get("metadata") or {})

            metadata.update({
                "policy_id": int(policy_id),
                "category": category,
                "chunk_index": chunk_index
            })

            records.append((
                int(policy_id),
                chunk_index,
                chunk["text"],
                Json(metadata),
                embedding
            ))

        # STEP 4: Insert chunks
        cur.executemany(
            """
            INSERT INTO policy_chunks (
                policy_id,
                chunk_index,
                chunk_text,
                metadata,
                embedding
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            records
        )

        conn.commit()

        print(
            f"Successfully inserted {len(records)} chunks "
            f"for policy ID {policy_id}"
        )

        return len(records)

    except Exception as e:
        conn.rollback()
        print("Error storing policy chunks:", str(e))
        raise
