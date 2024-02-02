# setup_database.py

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Access the database credentials from environment variables
db_username = os.getenv('DB_USERNAME')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Construct the DATABASE_URL from individual environment variables
DATABASE_URL = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Establish a connection to the database
conn = psycopg2.connect(DATABASE_URL)

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Define the SQL command to create the 'uploaded_files' table
create_table_command = """
CREATE TABLE IF NOT EXISTS uploaded_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    file_name VARCHAR(255),
    file_size INTEGER
);
"""

# Execute the SQL command
cursor.execute(create_table_command)

# Commit the changes to the database
conn.commit()

# Close the cursor and connection
cursor.close()
conn.close()

print("Database setup complete.")
