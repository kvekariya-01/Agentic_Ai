import psycopg2
from psycopg2 import sql

DATABASE_URL = "postgresql://postgres:vekariya2002@db.udftcdkerpezzoblentv.supabase.co:5432/postgres"

def create_table():
    try:
        # Connect to Supabase PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # SQL to create table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            role VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        cursor.execute(create_table_query)
        conn.commit()

        print("✅ Table created successfully")

    except Exception as e:
        print("❌ Error:", e)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table()
