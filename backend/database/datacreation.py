
from concect import cur, conn


# =====================================
# 1. REGISTER TABLE
# =====================================

q = """
CREATE TABLE IF NOT EXISTS register (
    employee_id       VARCHAR(100),
    full_name         VARCHAR(100),
    email             VARCHAR(254) PRIMARY KEY,
    designation       VARCHAR(100),
    date_of_birth     DATE,
    gender            VARCHAR(20),
    profile_picture   BYTEA,
    mobile            VARCHAR(20),
    password          VARCHAR(255),
    teamsmail         VARCHAR(100)
)
"""

cur.execute(q)
conn.commit()
print("Register Table created successfully")


# =====================================
# 2. ANNOUNCEMENTS TABLE
# =====================================

q = """
CREATE TABLE IF NOT EXISTS announcements (
    announcement_id SERIAL PRIMARY KEY,
    designation VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

cur.execute(q)
conn.commit()
print("Announcement Table created successfully")


# =====================================
# 3. POLICIES TABLE
# =====================================

q = """
CREATE TABLE IF NOT EXISTS policies (
    policy_id SERIAL PRIMARY KEY,
    description TEXT,
    category VARCHAR(100),
    file_name VARCHAR(255),
    file_data BYTEA,
    file_size BIGINT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

cur.execute(q)
conn.commit()
print("Policies Table created successfully")


# =====================================
# 4. ENABLE PGVECTOR EXTENSION
# =====================================

q = """
CREATE EXTENSION IF NOT EXISTS vector
"""

cur.execute(q)
conn.commit()
print("PGVector Extension enabled successfully")


# =====================================
# 5. POLICY CHUNKS TABLE
# =====================================

q = """
CREATE TABLE IF NOT EXISTS policy_chunks (
    chunk_id SERIAL PRIMARY KEY,

    policy_id INTEGER NOT NULL
        REFERENCES policies(policy_id),

    chunk_index INTEGER NOT NULL,

    chunk_text TEXT NOT NULL,

    metadata JSONB,

    embedding VECTOR(384),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (policy_id, chunk_index)
)
"""

cur.execute(q)
conn.commit()
print("Policy Chunks Table created successfully")
q = """
select * from announcements
    
"""

result=cur.execute(q)
conn.commit()
print(result)


