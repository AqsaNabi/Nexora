
import json

from database.recruitment_db import get_recruitment_connection


def create_recruitment_post(job_description):
    """
    Creates a recruitment post and returns its generated post ID.
    """

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
    image_urls=None
):
    """
    Saves Google Form details and generated image URLs.
    """

    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        image_urls = image_urls or []

        cursor.execute(
            """
            INSERT INTO recruitment_metadata (
                post_id,
                form_id,
                form_url,
                image_urls
            )
            VALUES (%s, %s, %s, %s::jsonb)
            RETURNING metadata_id;
            """,
            (
                post_id,
                form_id,
                form_url,
                json.dumps(image_urls)
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
    """
    Retrieves a recruitment post with its metadata.
    """

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
        raise Exception(f"Failed to retrieve recruitment post: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_applicants_by_post(post_id):
    """
    Retrieves all applicants associated with a recruitment post.
    Does not return the actual PDF bytes.
    """

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
        raise Exception(f"Failed to retrieve applicants: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
