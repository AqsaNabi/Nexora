
import os
import requests
from dotenv import load_dotenv

from model.announcement_agent import  generate_announcement,modify_announcement


from repository.announcement import save_announcement,fetch_latest_announcement


from database.concect import cur, conn

load_dotenv()


# ==========================================
# BREVO EMAIL CONFIGURATION
# ==========================================

BREVO_API_URL = os.getenv("BREVO_API_URL")

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

sender_email = os.getenv("EMAIL_ADDRESS")

sender_name = os.getenv(
    "EMAIL_SENDER_NAME",
    "Nexora HR"
)


# ==========================================
# ALLOWED DESIGNATIONS
# ==========================================

ALLOWED_DESIGNATIONS = [
    "Manager",
    "Team Lead",
    "Employee"
]


# ==========================================
# VALIDATE DESIGNATION
# ==========================================

def validate_designation(designation):

    if designation not in ALLOWED_DESIGNATIONS:

        raise ValueError(
            "Invalid designation selected. "
            "Choose Managers, Team Leaders "
            "or All Employees."
        )


# ==========================================
# GENERATE ANNOUNCEMENT
# ==========================================

def create_announcement(designation, prompt):

    validate_designation(designation)

    if not prompt or not prompt.strip():

        raise ValueError(
            "Prompt cannot be empty."
        )

    announcement = generate_announcement(
        prompt=prompt,
        designation=designation
    )

    return {
        "designation": designation,
        "announcement": announcement,
        "status": "pending",
        "saved": False,
        "email_sent": False
    }


# ==========================================
# MODIFY ANNOUNCEMENT
# ==========================================

def update_announcement(
    designation,
    existing_announcement,
    modification_prompt
):

    validate_designation(designation)

    if (
        not existing_announcement
        or not existing_announcement.strip()
    ):

        raise ValueError(
            "Existing announcement cannot be empty."
        )

    if (
        not modification_prompt
        or not modification_prompt.strip()
    ):

        raise ValueError(
            "Modification prompt cannot be empty."
        )

    revised_announcement = modify_announcement(
        announcement=existing_announcement,
        modification_prompt=modification_prompt,
        designation=designation
    )

    return {
        "designation": designation,
        "announcement": revised_announcement,
        "status": "pending",
        "saved": False,
        "email_sent": False
    }


# ==========================================
# REJECT ANNOUNCEMENT
# ==========================================

def reject_announcement(
    designation,
    title,
    announcement
):

    validate_designation(designation)

    print("\n========== REJECT ANNOUNCEMENT ==========")

    print("Designation:", designation)
    print("Title:", title)
    print("Announcement rejected successfully")

    return {
        "status": "rejected",
        "message": "Announcement rejected successfully",
        "designation": designation,
        "title": title
    }


# ==========================================
# GET EMPLOYEE RECIPIENTS
# ==========================================

def get_recipients(designation):

    validate_designation(designation)

    try:

        # -------------------------------------
        # ALL EMPLOYEES
        # -------------------------------------

        if designation == "Employee":

            query = """
                SELECT full_name, email
                FROM register
                WHERE email IS NOT NULL
                  AND designation <> 'hr';
            """

            cur.execute(query)

        # -------------------------------------
        # MANAGERS
        # -------------------------------------

        elif designation == "Manager":

            query = """
                SELECT full_name, email
                FROM register
                WHERE LOWER(TRIM(designation))
                IN (
                    'manager',
                    'Manager',
                    'managers'
                )
                AND email IS NOT NULL;
            """

            cur.execute(query)

        # -------------------------------------
        # TEAM LEADERS
        # -------------------------------------

        elif designation == "Team Lead":

            query = """
                SELECT full_name, email
                FROM register
                WHERE LOWER(TRIM(designation))
                IN (
                    'team leader',
                    'team leaders',
                    'tl',
                    'tls'
                )
                AND email IS NOT NULL;
            """

            cur.execute(query)

        # -------------------------------------
        # FETCH RECIPIENTS
        # -------------------------------------

        recipients = cur.fetchall()

        print(
            "Recipients fetched:",
            len(recipients)
        )

        return recipients

    except Exception as error:

        print(
            "Failed to fetch recipients:",
            repr(error)
        )

        raise


# ==========================================
# SEND ANNOUNCEMENT EMAIL USING BREVO
# ==========================================

def send_announcement_email(
    recipient_name,
    recipient_email,
    title,
    announcement
):

    # ======================================
    # CREATE EMAIL BODY
    # ======================================

    body = f"""
Dear {recipient_name},

{announcement}

Regards,

HR Department
"""

    # ======================================
    # VALIDATE BREVO CONFIGURATION
    # ======================================

    if not BREVO_API_KEY:

        raise ValueError(
            "BREVO_API_KEY is missing from environment variables."
        )

    if not sender_email:

        raise ValueError(
            "EMAIL_ADDRESS is missing from environment variables."
        )

    # ======================================
    # CREATE BREVO PAYLOAD
    # ======================================

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": recipient_email,
                "name": recipient_name
            }
        ],
        "subject": title,
        "textContent": body
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    # ======================================
    # SEND EMAIL THROUGH BREVO API
    # ======================================

    try:

        print(
            f"Sending announcement email to "
            f"{recipient_email} through Brevo..."
        )

        response = requests.post(
            BREVO_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        response_data = response.json()

        print(
            f"Brevo accepted email for {recipient_email}. "
            f"Message ID: "
            f"{response_data.get('messageId', 'not returned')}"
        )

        return True

    except requests.exceptions.RequestException as error:

        response_text = ""

        if error.response is not None:

            response_text = error.response.text

        print(
            f"Email sending failed for {recipient_email}: "
            f"{repr(error)} {response_text}"
        )

        raise


# ==========================================
# APPROVE ANNOUNCEMENT
# ==========================================

def approve_announcement(
    designation,
    title,
    announcement
):

    validate_designation(designation)

    if not title or not title.strip():

        raise ValueError(
            "Announcement title cannot be empty."
        )

    if not announcement or not announcement.strip():

        raise ValueError(
            "Announcement cannot be empty."
        )

    # ======================================
    # STEP 1: SAVE ANNOUNCEMENT
    # ======================================

    announcement_id = save_announcement(
        designation=designation,
        title=title,
        announcement=announcement
    )

    print("\n========== APPROVE ==========")

    print("Designation:", designation)
    print("Title:", title)
    print("Announcement saved successfully")

    # ======================================
    # STEP 2: FETCH RECIPIENTS
    # ======================================

    recipients = get_recipients(
        designation=designation
    )

    print(
        "Total recipients:",
        len(recipients)
    )

    # ======================================
    # STEP 3: SEND EMAILS
    # ======================================

    successful_emails = []
    failed_emails = []

    for recipient in recipients:

        recipient_name = recipient["full_name"]
        recipient_email = recipient["email"]

        try:

            send_announcement_email(
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                title=title,
                announcement=announcement
            )

            successful_emails.append(
                recipient_email
            )

        except Exception as error:

            print(
                f"Email failed for {recipient_email}: "
                f"{repr(error)}"
            )

            failed_emails.append({
                "email": recipient_email,
                "error": str(error)
            })

    # ======================================
    # STEP 4: EMAIL SUMMARY
    # ======================================

    print("\n========== EMAIL SUMMARY ==========")

    print(
        "Total recipients:",
        len(recipients)
    )

    print(
        "Emails sent:",
        len(successful_emails)
    )

    print(
        "Emails failed:",
        len(failed_emails)
    )

    print("Announcement approval completed")

    # ======================================
    # STEP 5: RETURN RESULT
    # ======================================

    return {
        "status": "approved",
        "announcement_id": announcement_id,
        "designation": designation,
        "title": title,
        "announcement": announcement,
        "total_recipients": len(recipients),
        "emails_sent": len(successful_emails),
        "emails_failed": len(failed_emails),
        "failed_emails": failed_emails,
        "saved": True
    }


# ==========================================
# GET LATEST ANNOUNCEMENT
# ==========================================

def get_latest_announcement(designation: str):

    if not designation or not designation.strip():

        raise ValueError(
            "Designation cannot be empty."
        )

    designation = designation.strip()

    result = fetch_latest_announcement(
        designation=designation
    )

    if not result:

        return {
            "designation": designation,
            "announcement": None,
            "message": (
                "No announcements found for this designation."
            )
        }

    return result
