from model.policy_embed import embedding_model
from model.llm_model import generate_answer

from repository.user_policy import search_policy_chunks


# =====================================================
# EMPLOYEE SERVICE: ASK POLICY QUESTION
# =====================================================

def ask_policy_question(
    question: str,
    category: str = None
):

    # ---------------------------------------------
    # STEP 1: Validate Question
    # ---------------------------------------------

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    question = question.strip()

    # Category is optional
    if category is not None:
        category = category.strip() or None


    # ---------------------------------------------
    # STEP 2: Generate Question Embedding
    # ---------------------------------------------

    question_embedding = embedding_model.embed_query(
        question
    )


    # ---------------------------------------------
    # STEP 3: Retrieve Relevant Chunks
    # ---------------------------------------------

    retrieved_chunks = search_policy_chunks(
        question_embedding=question_embedding,
        top_k=5,
        category=category
    )


    # ---------------------------------------------
    # STEP 4: Check Retrieved Results
    # ---------------------------------------------

    if not retrieved_chunks:

        return {
            "question": question,
            "category": category,
            "answer": (
                "I could not find relevant information "
                "in the available company policies."
            ),
            "sources": []
        }


    # ---------------------------------------------
    # STEP 5: Prepare Context and Sources
    # ---------------------------------------------

    context_parts = []
    sources = []

    for chunk in retrieved_chunks:

        chunk_text = chunk["chunk_text"]

        metadata = chunk.get("metadata") or {}

        context_parts.append(chunk_text)

        sources.append({
            "policy_id": chunk["policy_id"],
            "policy_name": metadata.get("policy_name"),
            "category": metadata.get("category"),
            "chunk_index": chunk["chunk_index"],
            "page_numbers": metadata.get("page_numbers", [])
        })


    context = "\n\n".join(context_parts)


    # ---------------------------------------------
    # STEP 6: Generate Answer Using Bedrock LLM
    # ---------------------------------------------

    answer = generate_answer(
        question=question,
        context=context
    )


    # ---------------------------------------------
    # STEP 7: Return Final Response
    # ---------------------------------------------

    return {
        "question": question,
        "category": category,
        "answer": answer,
        "sources": sources
    }