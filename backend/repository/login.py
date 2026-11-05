
from database.concect import cur, conn


def get_employee_by_email(email):
    cur.execute(
        """
        SELECT *
        FROM register
        WHERE LOWER(email) = %s
        """,
        (email.strip().lower(),)
    )

    return cur.fetchone()



