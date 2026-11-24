from fastapi import HTTPException
from psycopg2.extras import Json  # ✅ Added missing import
import traceback
 
from backend.database.concect import cur, conn
 
cursor = cur
connection = conn
 
def _safe_rollback():
    try:
        if connection:
            connection.rollback()
    except Exception:
        pass
 
# =========================================================
# 1. CANDIDATE EVALUATION
# =========================================================
def evaluate_candidate(resume_text, job_description):
    return {"candidate_score": None}
 
 
# =========================================================
# 2. GET DASHBOARD DATA
# =========================================================
def get_dashboard_data():
    # ✅ REMOVED: connection = None, cursor = None
    try:
        cursor.execute("""
            SELECT
                rp.post_id,
                rp.job_title,
                rp.job_description,
                TO_CHAR(rm.created_at, 'DD-MM-YYYY') AS job_posted_date,
                rm.metadata_id,
                rm.form_id,
                rm.form_url,
                rm.image_urls,
                rm.created_at,
                rm.updated_at
            FROM recruitment_posts rp
            LEFT JOIN recruitment_metadata rm
                ON rp.post_id = rm.post_id
            ORDER BY rm.created_at DESC NULLS LAST;
        """)
        combined_jobs = cursor.fetchall()
 
        cursor.execute("""
            SELECT COUNT(*) AS total_applicants
            FROM recruitment_data;
        """)
        total_applicants = cursor.fetchone()["total_applicants"]
 
        return {
            "jobs": combined_jobs,
            "total_jobs": len(combined_jobs),
            "total_applicants": total_applicants
        }
    except Exception as e:
        _safe_rollback()
        traceback.print_exc()
        raise e
 
 
# =========================================================
# 3. GET CANDIDATE APPLICATIONS
# =========================================================
def get_applications_data(post_id: str):
    try:
        cursor.execute("""
            SELECT post_id FROM recruitment_posts WHERE post_id = %s;
        """, (post_id,))
        selected_job = cursor.fetchone()
 
        if selected_job is None:
            raise HTTPException(status_code=404, detail="Job posting not found")
 
        cursor.execute("""
            SELECT
                application_id, post_id, full_name, email, phone,
                resume_filename, resume_content_type,
                (resume_file IS NOT NULL) AS has_resume,
                additional_data, submitted_at, candidate_score
            FROM recruitment_data
            WHERE post_id = %s
            ORDER BY submitted_at DESC;
        """, (post_id,))
        selected_applications = cursor.fetchall()
 
        for application in selected_applications:
            application["resume_file"] = None
 
        return {
            "post_id": post_id,
            "applications": selected_applications
        }
    except Exception as e:
        _safe_rollback()
        traceback.print_exc()
        raise e
 
 
# =========================================================
# 4. SUBMIT NEW CANDIDATE APPLICATION
# =========================================================
def submit_application_data(post_id: str, request):
    try:
        cursor.execute("""
            SELECT post_id, job_description FROM recruitment_posts WHERE post_id = %s;
        """, (post_id,))
        selected_job = cursor.fetchone()
 
        if selected_job is None:
            raise HTTPException(status_code=404, detail="Job posting not found")
 
        evaluation = evaluate_candidate(request.resume_text, selected_job["job_description"])
 
        cursor.execute("""
            INSERT INTO recruitment_data (
                post_id, full_name, email, phone,
                resume_file, resume_filename, resume_content_type,
                additional_data, candidate_score
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                application_id, post_id, full_name, email, phone,
                resume_filename, resume_content_type, additional_data,
                submitted_at, candidate_score;
        """, (
            post_id, request.full_name, request.email, request.phone,
            request.resume_file, request.resume_filename, request.resume_content_type,
            Json(request.additional_data),  # ✅ Now works because of the import
            evaluation["candidate_score"]
        ))
 
        new_application = dict(cursor.fetchone())
        connection.commit()
 
        new_application["resume_file"] = None
 
        return {
            "message": "Application submitted successfully",
            "application": new_application
        }
 
    except HTTPException:
        raise
    except Exception:
        _safe_rollback()
        traceback.print_exc()
        raise
 
 
# =========================================================
# 5. GET CANDIDATE RESUME
# =========================================================
def get_candidate_resume(application_id: int):
    try:
        cursor.execute("""
            SELECT resume_file, resume_filename, resume_content_type
            FROM recruitment_data
            WHERE application_id = %s;
        """, (application_id,))
        resume = cursor.fetchone()
 
        if resume is None:
            raise HTTPException(status_code=404, detail="Candidate application not found")
 
        if not resume["resume_file"]:
            raise HTTPException(status_code=404, detail="No resume has been added")
 
        return dict(resume)
    except Exception as e:
        _safe_rollback()
        traceback.print_exc()
        raise e