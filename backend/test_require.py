
# # # # from fastapi import FastAPI

# # # # from routes.google_forms import router as google_forms_router

# # # # app = FastAPI(
# # # #     title="Nexora Recruitment Module Testing",
# # # #     description="Independent testing environment for recruitment modules",
# # # #     version="1.0.0"
# # # # )

# # # # # Register Google Forms routes
# # # # app.include_router(google_forms_router)


# # # # @app.get("/")
# # # # def home():
# # # #     return {
# # # #         "message": "Nexora Recruitment Testing API is running!"
# # # #     }
# # # # from database.recruitment_db import get_recruitment_connection

# # # # connection = get_recruitment_connection()

# # # # print("Database connection test successful!")

# # # # connection.close()

# # # from database.recruitment_db import get_recruitment_connection


# # # def insert_dummy_post():
# # #     connection = get_recruitment_connection()
# # #     cursor = connection.cursor()

# # #     try:
# # #         job_description = """
# # #         Python Developer

# # #         Requirements:
# # #         - Knowledge of Python
# # #         - Knowledge of FastAPI
# # #         - Basic understanding of PostgreSQL
# # #         - Good problem-solving skills
# # #         """

# # #         cursor.execute(
# # #             """
# # #             INSERT INTO recruitment_posts (job_description)
# # #             VALUES (%s)
# # #             RETURNING post_id;
# # #             """,
# # #             (job_description,)
# # #         )

# # #         post_id = cursor.fetchone()[0]
# # #         connection.commit()

# # #         print("Recruitment post inserted successfully!")
# # #         print("Generated Post ID:", post_id)

# # #     except Exception as error:
# # #         connection.rollback()
# # #         print("Insertion failed:", error)
# # #         raise

# # #     finally:
# # #         cursor.close()
# # #         connection.close()


# # # if __name__ == "__main__":
# # #     insert_dummy_post()

# # import json

# # from database.recruitment_db import get_recruitment_connection


# # def insert_metadata():
# #     connection = get_recruitment_connection()
# #     cursor = connection.cursor()

# #     try:
# #         form_id = "DUMMY_FORM_001"
# #         form_url = "https://docs.google.com/forms/d/DUMMY_FORM_001/viewform"

# #         image_urls = [
# #             "https://example.com/recruitment-banner.png",
# #             "https://example.com/company-logo.png"
# #         ]

# #         cursor.execute(
# #             """
# #             INSERT INTO recruitment_metadata (
# #                 post_id,
# #                 form_id,
# #                 form_url,
# #                 image_urls
# #             )
# #             VALUES (%s, %s, %s, %s::jsonb)
# #             RETURNING metadata_id, post_id, created_at;
# #             """,
# #             (
# #                 "POST-000001",
# #                 form_id,
# #                 form_url,
# #                 json.dumps(image_urls)
# #             )
# #         )

# #         result = cursor.fetchone()
# #         connection.commit()

# #         print("Metadata inserted successfully!")
# #         print("Metadata ID:", result[0])
# #         print("Post ID:", result[1])
# #         print("Created At:", result[2])

# #     except Exception as error:
# #         connection.rollback()
# #         print("Metadata insertion failed:", error)
# #         raise

# #     finally:
# #         cursor.close()
# #         connection.close()


# # if __name__ == "__main__":
# #     insert_metadata()

# from pathlib import Path
# import json
# import psycopg2

# from database.recruitment_db import get_recruitment_connection


# # PDF file to test
# PDF_PATH = Path("storage/policy/Policy.pdf")


# def test_resume_storage():

#     if not PDF_PATH.exists():
#         raise FileNotFoundError(f"PDF not found: {PDF_PATH.resolve()}")

#     connection = get_recruitment_connection()
#     cursor = connection.cursor()

#     try:
#         # Read PDF as binary data
#         with open(PDF_PATH, "rb") as file:
#             resume_data = file.read()

#         # Dummy applicant information
#         applicant_name = "Test Applicant"
#         applicant_email = "test.applicant@example.com"
#         applicant_phone = "9876543210"

#         additional_data = {
#             "skills": ["Python", "FastAPI", "PostgreSQL"],
#             "experience": "Fresher"
#         }

#         # Insert applicant and actual PDF into PostgreSQL
#         cursor.execute(
#             """
#             INSERT INTO recruitment_data (
#                 post_id,
#                 full_name,
#                 email,
#                 phone,
#                 resume_file,
#                 resume_filename,
#                 resume_content_type,
#                 additional_data
#             )
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
#             RETURNING application_id;
#             """,
#             (
#                 "POST-000001",
#                 applicant_name,
#                 applicant_email,
#                 applicant_phone,
#                 psycopg2.Binary(resume_data),
#                 PDF_PATH.name,
#                 "application/pdf",
#                 json.dumps(additional_data)
#             )
#         )

#         application_id = cursor.fetchone()[0]
#         connection.commit()

#         print("Applicant inserted successfully!")
#         print("Application ID:", application_id)
#         print("Original PDF size:", len(resume_data), "bytes")

#         # Retrieve PDF from PostgreSQL
#         cursor.execute(
#             """
#             SELECT resume_file, resume_filename
#             FROM recruitment_data
#             WHERE application_id = %s;
#             """,
#             (application_id,)
#         )

#         stored_resume, filename = cursor.fetchone()

#         # Save retrieved PDF as a separate file
#         output_path = PDF_PATH.parent / "Policy_retrieved.pdf"

#         with open(output_path, "wb") as file:
#             file.write(bytes(stored_resume))

#         print("PDF retrieved successfully!")
#         print("Retrieved PDF size:", len(stored_resume), "bytes")
#         print("Retrieved file:", output_path.resolve())

#         # Verify original and retrieved contents
#         if resume_data == bytes(stored_resume):
#             print("SUCCESS: Original and retrieved PDFs are identical!")
#         else:
#             print("ERROR: PDF contents do not match!")

#     except Exception as error:
#         connection.rollback()
#         print("Test failed:", error)
#         raise

#     finally:
#         cursor.close()
#         connection.close()


# if __name__ == "__main__":
#     test_resume_storage()


from repository.recruitment_repository import (
    create_recruitment_post,
    save_recruitment_metadata,
    get_recruitment_post,
    get_applicants_by_post
)

# 1. Create a new recruitment post
post_id = create_recruitment_post(
    "Hiring Python Developer with FastAPI experience."
)

print("\nGenerated Post ID:", post_id)

# 2. Save Google Form metadata
metadata_id = save_recruitment_metadata(
    post_id=post_id,
    form_id="TEST_FORM_002",
    form_url="https://docs.google.com/forms/d/TEST_FORM_002/viewform",
    image_urls=[
        "https://example.com/job-image.png"
    ]
)

print("Metadata ID:", metadata_id)

# 3. Retrieve recruitment post
post = get_recruitment_post(post_id)

print("\nRecruitment Post:")
print(post)

# 4. Retrieve applicants
applicants = get_applicants_by_post(post_id)

print("\nApplicants:")
print(applicants)
