import json
import traceback

from backend.database.concect import cur, conn

cursor = cur
connection = conn


def _get(row, key):
    """Read a column from a RealDictCursor row or a plain tuple row."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    return row[0]


def _safe_rollback():
    try:
        if connection:
            connection.rollback()
    except Exception:
        pass


# ---------------------------------------------------------------- create

def create_recruitment_post(job_title, job_description):
    try:
        cursor.execute(
            """
            INSERT INTO recruitment_posts (
                job_title,
                job_description
            )
            VALUES (%s, %s)
            RETURNING post_id;
            """,
            (job_title, job_description),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("INSERT ... RETURNING post_id returned no row")
        post_id = _get(row, "post_id")  # ✅ MUST BE THIS
        connection.commit()             # ✅ MUST BE THIS
        return post_id
    except Exception as error:
        traceback.print_exc()
        _safe_rollback()
        raise Exception(
            f"Failed to create recruitment post: "
            f"{type(error).__name__}: {error!r}"
        ) from error
# ---------------------------------------------------------------- metadata

def save_recruitment_metadata(
    post_id,
    form_id=None,
    form_url=None,
    image_urls=None,
    question_mapping=None,
    application_form=None,
):
    try:
        # Pre-check: turn the opaque FK error into a clear, actionable message.
        cursor.execute(
            "SELECT 1 AS ok FROM recruitment_posts WHERE post_id = %s;",
            (post_id,),
        )
        if cursor.fetchone() is None:
            # Help the caller see what IS in the table
            cursor.execute(
                "SELECT post_id FROM recruitment_posts "
                "ORDER BY post_id DESC LIMIT 5;"
            )
            recent = [
                (_get(r, "post_id"))
                for r in cursor.fetchall()
            ]
            raise ValueError(
                f"post_id {post_id!r} does not exist in recruitment_posts.\n"
                f"Most recent post_ids in the table: {recent}\n"
                f"You must pass the exact value returned by "
                f"create_recruitment_post() — do NOT format it as "
                f"'POST-XXXXXX' first."
            )

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
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
            RETURNING metadata_id;
            """,
            (
                post_id,
                form_id,
                form_url,
                json.dumps(image_urls or []),
                json.dumps(question_mapping or {}),
                json.dumps(application_form or {}),
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError(
                "INSERT ... RETURNING metadata_id returned no row"
            )
        metadata_id = _get(row, "metadata_id")
        connection.commit()
        return metadata_id
    except Exception as error:
        traceback.print_exc()
        _safe_rollback()
        raise Exception(
            f"Failed to save recruitment metadata: "
            f"{type(error).__name__}: {error!r}"
        ) from error


# ---------------------------------------------------------------- reads

def get_recruitment_post(post_id):
    try:
        cursor.execute(
            """
            SELECT
                p.post_id,
                p.job_title,
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
            (post_id,),
        )
        result = cursor.fetchone()
        if not result:
            return None
        return {
            "post_id": _get(result, "post_id"),
            "job_title": _get(result, "job_title"),
            "job_description": _get(result, "job_description"),
            "form_id": _get(result, "form_id"),
            "form_url": _get(result, "form_url"),
            "image_urls": _get(result, "image_urls"),
            "created_at": _get(result, "created_at"),
        }
    except Exception as error:
        raise Exception(
            f"Failed to retrieve recruitment post: {error}"
        ) from error


def get_job_description(post_id):
    try:
        cursor.execute(
            """
            SELECT job_description
            FROM recruitment_posts
            WHERE post_id = %s;
            """,
            (post_id,),
        )
        result = cursor.fetchone()
        return _get(result, "job_description") if result else None
    except Exception as error:
        raise Exception(
            f"Failed to retrieve job description: {error}"
        ) from error


def get_applicants_by_post(post_id):
    try:
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
                submitted_at,
                candidate_score
            FROM recruitment_data
            WHERE post_id = %s
            ORDER BY submitted_at DESC;
            """,
            (post_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "application_id": _get(row, "application_id"),
                "post_id": _get(row, "post_id"),
                "full_name": _get(row, "full_name"),
                "email": _get(row, "email"),
                "phone": _get(row, "phone"),
                "resume_filename": _get(row, "resume_filename"),
                "resume_content_type": _get(row, "resume_content_type"),
                "additional_data": _get(row, "additional_data"),
                "submitted_at": _get(row, "submitted_at"),
                "candidate_score": _get(row, "candidate_score"),
            }
            for row in rows
        ]
    except Exception as error:
        raise Exception(
            f"Failed to retrieve applicants: {error}"
        ) from error


# ---------------------------------------------------------------- resume

def attach_resume_to_applicant(
    post_id,
    email,
    resume_content,
    resume_filename,
    resume_content_type,
):
    try:
        cursor.execute(
            """
            SELECT application_id
            FROM recruitment_data
            WHERE post_id = %s
              AND LOWER(TRIM(email)) = LOWER(TRIM(%s));
            """,
            (post_id, email),
        )
        applicants = cursor.fetchall()

        if not applicants:
            return {
                "success": False,
                "message": (
                    "Application details have not been received yet. "
                    "Please try again shortly."
                ),
            }

        if len(applicants) > 1:
            return {
                "success": False,
                "message": (
                    "Multiple applications were found for this email "
                    "and recruitment post. Please contact HR."
                ),
            }

        application_id = _get(applicants[0], "application_id")

        cursor.execute(
            """
            SELECT resume_file
            FROM recruitment_data
            WHERE application_id = %s;
            """,
            (application_id,),
        )
        resume_row = cursor.fetchone()
        existing_resume = _get(resume_row, "resume_file") if resume_row else None

        if existing_resume is not None:
            return {
                "success": False,
                "message": (
                    "A resume has already been uploaded for this application."
                ),
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
                application_id,
            ),
        )
        connection.commit()
        return {
            "success": True,
            "message": "Resume uploaded successfully.",
            "application_id": application_id,
        }
    except Exception:
        traceback.print_exc()
        _safe_rollback()
        raise