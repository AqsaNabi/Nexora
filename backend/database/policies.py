CREATE TABLE policies (
    policy_id BIGSERIAL PRIMARY KEY,
    policy_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) UNIQUE NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_data BYTEA NOT NULL,
    file_size BIGINT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)