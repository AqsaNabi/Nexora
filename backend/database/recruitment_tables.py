
import json

from backend.database.recruitment_db import get_recruitment_connection


# ============================================================
# CREATE RECRUITMENT POST
# ============================================================

def create_recruitment_post(job_description):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO recruitment_posts (job_description)
            VALUES (%s)
            RETURNING post_id;
            """,
            (job_description,)
        )

        post_id = cursor.fetchone()[0]
        connection.commit()

        return post_id

    except Exception as error:
        if connection:
            connection.rollback()
        raise Exception(f"Failed to create recruitment post: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# SAVE RECRUITMENT METADATA
# ============================================================

def save_recruitment_metadata(
    post_id,
    form_id=None,
    form_url=None,
    image_urls=None,
    question_mapping=None,
    application_form=None
):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO recruitment_metadata (
                post_id,
                form_id,
                form_url,
                image_urls,
                question_mapping,
                application_form
            )
            VALUES (
                %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb
            )
            RETURNING metadata_id;
            """,
            (
                post_id,
                form_id,
                form_url,
                json.dumps(image_urls or []),
                json.dumps(question_mapping or {}),
                json.dumps(application_form or {})
            )
        )

        metadata_id = cursor.fetchone()[0]
        connection.commit()

        return metadata_id

    except Exception as error:
        if connection:
            connection.rollback()
        raise Exception(
            f"Failed to save recruitment metadata: {error}"
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# GET RECRUITMENT POST
# ============================================================

def get_recruitment_post(post_id):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                p.post_id,
                p.job_description,
                m.form_id,
                m.form_url,
                m.image_urls,
                m.created_at
            FROM recruitment_posts p
            LEFT JOIN recruitment_metadata m
                ON p.post_id = m.post_id
            WHERE p.post_id = %s;
            """,
            (post_id,)
        )

        result = cursor.fetchone()

        if not result:
            return None

        return {
            "post_id": result[0],
            "job_description": result[1],
            "form_id": result[2],
            "form_url": result[3],
            "image_urls": result[4],
            "created_at": result[5]
        }

    except Exception as error:
        raise Exception(
            f"Failed to retrieve recruitment post: {error}"
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# GET APPLICANTS BY RECRUITMENT POST
# ============================================================

def get_applicants_by_post(post_id):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                application_id,
                post_id,
                full_name,
                email,
                phone,
                resume_filename,
                resume_content_type,
                additional_data,
                submitted_at
            FROM recruitment_data
            WHERE post_id = %s
            ORDER BY submitted_at DESC;
            """,
            (post_id,)
        )

        rows = cursor.fetchall()

        return [
            {
                "application_id": row[0],
                "post_id": row[1],
                "full_name": row[2],
                "email": row[3],
                "phone": row[4],
                "resume_filename": row[5],
                "resume_content_type": row[6],
                "additional_data": row[7],
                "submitted_at": row[8]
            }
            for row in rows
        ]

    except Exception as error:
        raise Exception(
            f"Failed to retrieve applicants: {error}"
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# SAVE RESUME AGAINST EXISTING APPLICANT
# ============================================================

def attach_resume_to_applicant(
    post_id,
    email,
    resume_content,
    filename,
    content_type
):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE recruitment_data
            SET
                resume_file = %s,
                resume_filename = %s,
                resume_content_type = %s
            WHERE post_id = %s
              AND LOWER(TRIM(email)) = LOWER(TRIM(%s))
            RETURNING application_id;
            """,
            (
                resume_content,
                filename,
                content_type,
                post_id,
                email
            )
        )

        result = cursor.fetchone()

        if not result:
            connection.rollback()
            return None

        connection.commit()

        return result[0]

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# SAVE PENDING RESUME
# ============================================================

def save_pending_resume(
    post_id,
    email,
    resume_content,
    filename,
    content_type
):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO recruitment_pending_resumes (
                post_id,
                email,
                resume_file,
                resume_filename,
                resume_content_type
            )
            VALUES (%s, LOWER(TRIM(%s)), %s, %s, %s)
            ON CONFLICT (post_id, email)
            DO UPDATE SET
                resume_file = EXCLUDED.resume_file,
                resume_filename = EXCLUDED.resume_filename,
                resume_content_type = EXCLUDED.resume_content_type,
                uploaded_at = CURRENT_TIMESTAMP;
            """,
            (
                post_id,
                email,
                resume_content,
                filename,
                content_type
            )
        )

        connection.commit()

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# ATTACH PENDING RESUME AFTER APPLICANT INSERTION
# ============================================================

def attach_pending_resume(post_id, email, cursor):
    cursor.execute(
        """
        SELECT
            resume_file,
            resume_filename,
            resume_content_type
        FROM recruitment_pending_resumes
        WHERE post_id = %s
          AND email = LOWER(TRIM(%s))
        FOR UPDATE;
        """,
        (post_id, email)
    )

    pending_resume = cursor.fetchone()

    if not pending_resume:
        return False

    cursor.execute(
        """
        UPDATE recruitment_data
        SET
            resume_file = %s,
            resume_filename = %s,
            resume_content_type = %s
        WHERE post_id = %s
          AND LOWER(TRIM(email)) = LOWER(TRIM(%s));
        """,
        (
            pending_resume[0],
            pending_resume[1],
            pending_resume[2],
            post_id,
            email
        )
    )

    cursor.execute(
        """
        DELETE FROM recruitment_pending_resumes
        WHERE post_id = %s
          AND email = LOWER(TRIM(%s));
        """,
        (post_id, email)
    )

    return True
