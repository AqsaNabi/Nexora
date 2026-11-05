from backend.database.concect import cur ,conn  
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
print("Table created successfully")


conn.commit()