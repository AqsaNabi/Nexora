
from services.google_form_service import create_google_form_from_json


# Sample AI-generated JSON
sample_data = {
    "job_post": {
        "job_title": "Python Developer",
        "job_description": (
            "We are hiring a Python Developer "
            "with experience in FastAPI."
        )
    },

    "application_form": {
        "form_title": "Python Developer Application",

        "questions": [
            {
                "field_name": "full_name",
                "question": "Enter your full name",
                "type": "text",
                "required": True,
                "options": []
            },
            {
                "field_name": "email",
                "question": "Enter your email",
                "type": "email",
                "required": True,
                "options": []
            },
            {
                "field_name": "phone",
                "question": "Enter your phone number",
                "type": "text",
                "required": True,
                "options": []
            },
            {
                "field_name": "resume_file",
                "question": "Upload your resume PDF",
                "type": "file",
                "required": True,
                "options": []
            },
            {
                "field_name": "python_experience",
                "question": "How many years of Python experience do you have?",
                "type": "text",
                "required": True,
                "options": []
            },
            {
                "field_name": "github_link",
                "question": "Enter your GitHub profile",
                "type": "url",
                "required": False,
                "options": []
            }
        ]
    }
}


# Create the form and automatically rename its Drive file
result = create_google_form_from_json(sample_data)


print("\nGOOGLE FORM CREATED SUCCESSFULLY!")
print("----------------------------------")

print("Form ID:", result["form_id"])
print("Form Title:", result["title"])
print("Drive File Name:", result["drive_file_name"])
print("Form URL:", result["form_url"])

print("\nSkipped Questions:")
print(result["skipped_questions"])
