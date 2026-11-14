
from database.concect import conn, cur
from psycopg2 import Binary
from psycopg2.extras import Json

from pgvector.psycopg2 import register_vector

from model.policy_embed import embedding_model


# ==========================================
# PGVECTOR CONFIGURATION
# ==========================================

# Register pgvector with the existing connection
register_vector(conn)


# ==========================================
# STORE POLICY IN POSTGRESQL
# ==========================================

def create_policy(
    policy_name,
    description,
    category,
    file_name,
    file_data,
    file_size
):

    try:
        cur.execute(
            """
            INSERT INTO policies (
                policy_name,
                description,
                category,
                file_name,
                file_data,
                file_size,
                uploaded_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)

            ON CONFLICT (category)
            DO UPDATE SET
                policy_name = EXCLUDED.policy_name,
                description = EXCLUDED.description,
                file_name = EXCLUDED.file_name,
                file_data = EXCLUDED.file_data,
                file_size = EXCLUDED.file_size,
                uploaded_at = CURRENT_TIMESTAMP

            RETURNING policy_id
            """,
            (
                policy_name,
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
            "policy_name": policy_name,
            "category": category,
            "file_name": file_name,
            "file_size": file_size,
            "message": "Policy uploaded or updated successfully"
        }

    except Exception as e:
        conn.rollback()
        raise e


# ==========================================
# STORE POLICY CHUNKS IN PGVECTOR
# ==========================================

def create_policy_chunks(
    policy_id,
    policy_name,
    category,
    chunks
):

    if not chunks:
        raise ValueError("No chunks available to store.")

    try:

        # STEP 1: Generate embeddings for chunks

        embeddings = embedding_model.embed_documents(chunks)

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Number of embeddings does not match number of chunks."
            )

        # STEP 2: Delete existing chunks of this policy

        cur.execute(
            """
            DELETE FROM policy_chunks
            WHERE policy_id = %s
            """,
            (int(policy_id),)
        )

        # STEP 3: Prepare chunk metadata

        records = []

        for i, chunk in enumerate(chunks):

            metadata = {
                "policy_id": int(policy_id),
                "policy_name": policy_name,
                "category": category,
                "chunk_index": i
            }

            records.append((
                int(policy_id),
                i,
                chunk,
                Json(metadata),
                embeddings[i]
            ))

        # STEP 4: Insert chunks and embeddings into PostgreSQL

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

        # STEP 5: Commit transaction

        conn.commit()

        print(
            f"Successfully stored {len(chunks)} chunks "
            f"for policy ID {policy_id}"
        )

        return len(chunks)

    except Exception as e:

        conn.rollback()

        print("Error storing policy chunks:", e)

        raise
