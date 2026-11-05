import psycopg2
from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Salif@523186",
        port="5432",
        database="nexora",
        cursor_factory=RealDictCursor 
    )

    cur = conn.cursor()

    print("Connected to database PostgreSQL successfully!")

except psycopg2.Error as e:
    print(f"Database connection failed: {e}")
    raise
