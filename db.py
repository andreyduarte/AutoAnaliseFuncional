import sqlite3
import uuid
from datetime import datetime

DATABASE_NAME = 'analysis_database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_uuid TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            narrative_text TEXT NOT NULL,
            analysis_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create an index on analysis_uuid for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_analysis_uuid ON analyses (analysis_uuid)
    ''')
    conn.commit()
    conn.close()

def insert_analysis(name: str, narrative_text: str, analysis_data: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    new_uuid = str(uuid.uuid4())
    try:
        cursor.execute(
            "INSERT INTO analyses (analysis_uuid, name, narrative_text, analysis_data, created_at) VALUES (?, ?, ?, ?, ?)",
            (new_uuid, name, narrative_text, analysis_data, datetime.now())
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        # Re-raise the exception to be handled by the caller
        raise e
    finally:
        conn.close()
    return new_uuid

def get_analysis_by_uuid(analysis_uuid: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE analysis_uuid = ?", (analysis_uuid,))
    analysis = cursor.fetchone()
    conn.close()
    return analysis

def get_all_analyses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, analysis_uuid, name, created_at FROM analyses ORDER BY created_at DESC")
    analyses = cursor.fetchall()
    conn.close()
    return analyses

if __name__ == '__main__':
    # This will initialize the database and table if the script is run directly
    init_db()
    print(f"Database '{DATABASE_NAME}' initialized and 'analyses' table created/verified.")
    # Example usage (optional, for testing)
    # try:
    #     test_uuid = insert_analysis("Test Analysis", "This is a test narrative.", '{"key": "value"}')
    #     print(f"Inserted test analysis with UUID: {test_uuid}")
    #     retrieved_analysis = get_analysis_by_uuid(test_uuid)
    #     print(f"Retrieved test analysis: {retrieved_analysis['name'] if retrieved_analysis else 'Not found'}")
    #     all_analyses = get_all_analyses()
    #     print(f"Total analyses: {len(all_analyses)}")
    # except sqlite3.Error as e:
    #     print(f"An error occurred: {e}")
