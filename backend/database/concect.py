
import psycopg2
from psycopg2.extras import RealDictCursor



DATABASE_URL = "postgresql://root:yJGhhpuHeBL79s9n2vmc3ENk2w8ZrIJs@dpg-dbrasvdbedkc73d2l2bg-a.oregon-postgres.render.com/nexora_database_z4z0"

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
