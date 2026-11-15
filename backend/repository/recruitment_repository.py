
import json

from backend.database.recruitment_db import get_recruitment_connection


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
                post_id, form_id, form_url, image_urls,
                question_mapping, application_form
            )
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
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
        raise Exception(f"Failed to save recruitment metadata: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_recruitment_post(post_id):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT p.post_id, p.job_description, m.form_id,
                   m.form_url, m.image_urls, m.created_at
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
        raise Exception(f"Failed to retrieve recruitment post: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_applicants_by_post(post_id):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT application_id, post_id, full_name, email, phone,
                   resume_filename, resume_content_type,
                   additional_data, submitted_at
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
        raise Exception(f"Failed to retrieve applicants: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def attach_resume_to_applicant(
    post_id,
    email,
    resume_content,
    resume_filename,
    resume_content_type
):
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        # Find the applicant for this specific recruitment post.
        cursor.execute(
            """
            SELECT application_id
            FROM recruitment_data
            WHERE post_id = %s
              AND LOWER(TRIM(email)) = LOWER(TRIM(%s));
            """,
            (post_id, email)
        )

        applicants = cursor.fetchall()

        if not applicants:
            return {
                "success": False,
                "message": (
                    "Application details have not been received yet. "
                    "Please try again shortly."
                )
            }

        if len(applicants) > 1:
            return {
                "success": False,
                "message": (
                    "Multiple applications were found for this email "
                    "and recruitment post. Please contact HR."
                )
            }

        application_id = applicants[0][0]

        # Do not silently overwrite an already uploaded resume.
        cursor.execute(
            """
            SELECT resume_file
            FROM recruitment_data
            WHERE application_id = %s;
            """,
            (application_id,)
        )

        existing_resume = cursor.fetchone()[0]

        if existing_resume is not None:
            return {
                "success": False,
                "message": "A resume has already been uploaded for this application."
            }

        cursor.execute(
            """
            UPDATE recruitment_data
            SET resume_file = %s,
                resume_filename = %s,
                resume_content_type = %s
            WHERE application_id = %s;
            """,
            (
                resume_content,
                resume_filename,
                resume_content_type,
                application_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Resume uploaded successfully.",
            "application_id": application_id
        }

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
