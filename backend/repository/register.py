from database.concect import cur, conn
import streamlit as st

def create_employee(employee):

    try:

        q = """
            INSERT INTO register (
                employee_id,
                full_name,
                email,
                designation,
                date_of_birth,
                gender,
                profile_picture,
                mobile,
                password,
                teamsmail
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING employee_id, full_name, email
        """

        cur.execute(q, (
            employee["employee_id"],
            employee["full_name"],
            employee["email"],
            employee["designation"],
            employee["date_of_birth"],
            employee["gender"],
            employee["profile_picture"],
            employee["mobile"],
            employee["password"],
            employee["teamsmail"]
        ))

        

        conn.commit()
        
        

    except Exception as e:
        conn.rollback()
        raise e