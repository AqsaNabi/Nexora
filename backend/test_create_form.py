from services.google_form_service import create_google_form

result = create_google_form("Nexora - Test Recruitment Form")

print("\nGoogle Form Created Successfully!")
print("Form ID:", result["form_id"])
print("Form URL:", result["form_url"])