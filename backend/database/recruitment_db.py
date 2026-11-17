
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")


def get_recruitment_connection():
    database_url = ("postgresql://nexora_recruitment_user:6awt8vpC6y2NntJzl9e6MiwvnNowMePt@dpg-dbtdpo9srm7s73b0cu5g-a.virginia-postgres.render.com/nexora_recruitment")

    if not database_url:
        raise ValueError("RECRUITMENT_DATABASE_URL is missing from .env")

    connection = psycopg2.connect(
        database_url,
        sslmode="require"
    )

    return connection
