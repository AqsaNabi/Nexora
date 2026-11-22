
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor,
        sslmode="require"
    )

    cur = conn.cursor()

    print("Connected to Render PostgreSQL successfully!")

except psycopg2.Error as e:
    print(f"Database connection failed: {e}")
    raise
