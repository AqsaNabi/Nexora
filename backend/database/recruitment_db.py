
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def get_recruitment_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv("RECRUITMENT_DB_HOST"),
            port=os.getenv("RECRUITMENT_DB_PORT"),
            database=os.getenv("RECRUITMENT_DB_NAME"),
            user=os.getenv("RECRUITMENT_DB_USER"),
            password=os.getenv("RECRUITMENT_DB_PASSWORD")
        )

        print("Recruitment database connected successfully!")
        return connection

    except psycopg2.Error as error:
        print(f"Recruitment database connection failed: {error}")
        raise
