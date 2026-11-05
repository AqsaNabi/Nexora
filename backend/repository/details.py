from database.concect import cur, conn


def count_employee():
    cur.execute("""
        SELECT COUNT(*) AS total
        FROM register
    """)

    result = cur.fetchone()
    return result["total"]


def show_employees():

    cur.execute("""
        SELECT
            
            full_name,
            email,
            designation,
            date_of_birth,
            gender,
            mobile,
            teamsmail
        FROM register
    """)

    result = cur.fetchall()

    return result