
from database.concect import cur, conn


# ==========================================
# SAVE ANNOUNCEMENT
# ==========================================

def save_announcement(
    designation,
    title,
    announcement
):

    try:

        # ==========================================
        # RESET PREVIOUS FAILED TRANSACTION
        # ==========================================

        conn.rollback()

        print("Previous transaction reset")

        # ==========================================
        # INSERT ANNOUNCEMENT
        # ==========================================

        query = """
            INSERT INTO announcements (
                designation,
                title,
                content,
                created_at
            )
            VALUES (
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP
            )
            RETURNING announcement_id;
        """

        print("Executing announcement INSERT")

        cur.execute(
            query,
            (
                designation,
                title,
                announcement
            )
        )

        # ==========================================
        # GET INSERTED ID
        # ==========================================

        result = cur.fetchone()

        if result is None:

            raise Exception(
                "Announcement ID was not returned"
            )

        announcement_id = result["announcement_id"]

        # ==========================================
        # COMMIT
        # ==========================================

        conn.commit()

        print(
            "Announcement saved successfully:",
            announcement_id
        )

        return announcement_id

    except Exception as error:

        # ==========================================
        # ROLLBACK
        # ==========================================

        conn.rollback()

        print(
            "ANNOUNCEMENT DATABASE ERROR:",
            repr(error)
        )

        raise
# ==========================================
# FETCH LATEST ANNOUNCEMENT
# ==========================================

def fetch_latest_announcement(designation):

    try:

        # ==========================================
        # RESET PREVIOUS FAILED TRANSACTION
        # ==========================================

        conn.rollback()

        # ==========================================
        # FETCH LATEST ANNOUNCEMENT
        # ==========================================

        query = """
            SELECT
                announcement_id,
                designation,
                title,
                content,
                created_at

            FROM announcements

            WHERE designation = %s
            or designation='Employee'

            ORDER BY created_at DESC

            LIMIT 1;
        """

        cur.execute(
            query,
            (designation,)
        )

        result = cur.fetchone()

        # ==========================================
        # RETURN RESULT
        # ==========================================

        if result is None:
            return None

        return dict(result)

    except Exception as error:

        conn.rollback()

        print(
            "FETCH ANNOUNCEMENT ERROR:",
            repr(error)
        )

        raise
