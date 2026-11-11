
from database.recruitment_db import get_recruitment_connection


def create_recruitment_tables():
    connection = None
    cursor = None

    try:
        connection = get_recruitment_connection()
        cursor = connection.cursor()

        # 1. Recruitment posts
        cursor.execute("""
            CREATE SEQUENCE IF NOT EXISTS recruitment_post_id_seq
            START WITH 1 INCREMENT BY 1;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruitment_posts (
                post_id VARCHAR(20) PRIMARY KEY
                    DEFAULT (
                        'POST-' ||
                        LPAD(
                            NEXTVAL('recruitment_post_id_seq')::TEXT,
                            6,
                            '0'
                        )
                    ),
                job_description TEXT NOT NULL
            );
        """)

        # 2. Universal applicant data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruitment_data (
                application_id BIGSERIAL PRIMARY KEY,
                post_id VARCHAR(20) NOT NULL,
                full_name VARCHAR(150) NOT NULL,
                email VARCHAR(150) NOT NULL,
                phone VARCHAR(20),
                resume_file BYTEA,
                resume_filename VARCHAR(255),
                resume_content_type VARCHAR(100),
                additional_data JSONB DEFAULT '{}'::jsonb,
                submitted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_recruitment_post
                    FOREIGN KEY (post_id)
                    REFERENCES recruitment_posts(post_id)
                    ON DELETE CASCADE
            );
        """)

        # 3. Recruitment metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruitment_metadata (
                metadata_id BIGSERIAL PRIMARY KEY,
                post_id VARCHAR(20) NOT NULL UNIQUE,
                form_id VARCHAR(255),
                form_url TEXT,
                image_urls JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_metadata_post
                    FOREIGN KEY (post_id)
                    REFERENCES recruitment_posts(post_id)
                    ON DELETE CASCADE
            );
        """)

        connection.commit()

        print("All three recruitment tables created successfully!")

    except Exception as error:
        if connection:
            connection.rollback()

        print(f"Table creation failed: {error}")
        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    create_recruitment_tables()
