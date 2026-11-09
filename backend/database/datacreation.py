from concect import cur ,conn  
q="""CREATE TABLE IF NOT EXISTS register(
    employee_id       VARCHAR(100) ,
    full_name         VARCHAR(100),
    email             VARCHAR(254) primary key,
    designation       VARCHAR(100),
    date_of_birth     DATE,
    gender            VARCHAR(20),
    profile_picture     BYTEA,
    mobile            VARCHAR(20),
    password          VARCHAR(255),
    teamsmail          VARCHAR(100)
)"""

cur.execute(q)
print(" Register Table created successfully")


conn.commit()
q="""CREATE TABLE IF NOT EXISTS announcements (
 
    announcement_id SERIAL PRIMARY KEY,
 
    designation VARCHAR(50) NOT NULL,
 
    title VARCHAR(200) NOT NULL,
 
    content TEXT NOT NULL,
 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
 
)"""
cur.execute(q)
print("Announcemet Table created successfully")
conn.commit()