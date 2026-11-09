
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from model.announcement_agent import  generate_announcement, modify_announcement
   
   


from repository.announcement import save_announcement

from database.concect import cur, conn


# ==========================================
# EMAIL CONFIGURATION
# ==========================================

# Use your complete Gmail address
sender_email = "salifsajad1@gmail.com"

# Use your NEW Google App Password
sender_password = "dfbo rnfz mxxc"

smtp_server = "smtp.gmail.com"

smtp_port = 587


# ==========================================
# ALLOWED DESIGNATIONS
# ==========================================

ALLOWED_DESIGNATIONS = [

    "Managers",

    "Team Leaders",

    "All Employees"

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

def create_announcement(

    designation,

    prompt

):

    validate_designation(designation)

    if not prompt or not prompt.strip():

        raise ValueError(
            "Prompt cannot be empty."
        )

    # Generate announcement using AI
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

    if not existing_announcement or not existing_announcement.strip():

        raise ValueError(
            "Existing announcement cannot be empty."
        )

    if not modification_prompt or not modification_prompt.strip():

        raise ValueError(
            "Modification prompt cannot be empty."
        )

    # Modify announcement using AI
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

        if designation == "All Employees":

            query = """

                SELECT full_name, email

                FROM register

                WHERE email IS NOT NULL

                

            """

            cur.execute(query)

        # -------------------------------------
        # MANAGERS
        # -------------------------------------

        elif designation == "Managers":

            query = """

                SELECT full_name, email

                FROM register

                WHERE LOWER(TRIM(designation))

                IN (

                    'manager',

                    'managers'

                )

                AND email IS NOT NULL

                

            """

            cur.execute(query)

        # -------------------------------------
        # TEAM LEADERS
        # -------------------------------------

        elif designation == "Team Leaders":

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

                AND email IS NOT NULL

                

            """

            cur.execute(query)

        # -------------------------------------
        # FETCH EMPLOYEES
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
# SEND ANNOUNCEMENT EMAIL
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
    # CREATE EMAIL MESSAGE
    # ======================================

    message = MIMEMultipart()

    message["From"] = sender_email

    message["To"] = recipient_email

    message["Subject"] = title

    message.attach(

        MIMEText(

            body,

            "plain"

        )

    )

    # ======================================
    # SEND EMAIL
    # ======================================

    server = None

    try:

        print(
            "\nConnecting to Gmail SMTP server..."
        )

        server = smtplib.SMTP(

            smtp_server,

            smtp_port,

            timeout=30

        )

        # Secure connection
        server.starttls()

        print("Logging into Gmail...")

        # Login using Gmail and App Password
        server.login(

            sender_email,

            sender_password

        )

        print("Sending email...")

        # Send email
        server.send_message(message)

        print(
            f"Email sent successfully to {recipient_email}"
        )

        return True

    except Exception as error:

        print(
            f"Email sending failed for {recipient_email}: "
            f"{repr(error)}"
        )

        raise

    finally:

        if server is not None:

            try:

                server.quit()

            except Exception:

                pass


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
