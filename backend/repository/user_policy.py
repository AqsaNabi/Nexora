from database.concect import conn
from psycopg2.extras import RealDictCursor


def search_policy_chunks(
    question_embedding,
    top_k: int = 5,
    category: str = None
):
    """
    Retrieve relevant policy chunks using pgvector cosine distance.

    If category is None, search across all policy categories.
    """

    # Convert embedding list into pgvector format
    embedding_string = "[" + ",".join(
        str(float(value)) for value in question_embedding
    ) + "]"

    query = """ 
        SELECT
            id,
            policy_id,
            chunk_index,
            chunk_text,
            metadata,
            embedding <=> %s::vector AS distance

        FROM policy_chunks

        WHERE (
            %s IS NULL
            OR metadata->>'category' = %s
        )

        ORDER BY embedding <=> %s::vector

        LIMIT %s;
    """

    params = (
        embedding_string,
        category,
        category,
        embedding_string,
        top_k
    )

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute(query, params)

            results = cur.fetchall()

            return [dict(row) for row in results]

    except Exception as e:
        raise Exception(
            f"Policy chunk retrieval failed: {str(e)}"
        )