import os
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

def insert_analysis(name: str, analysis_data: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    new_uuid = str(uuid.uuid4())
    try:
        cursor.execute(
            "INSERT INTO analyses (analysis_uuid, name, analysis_data) VALUES (?, ?, ?)",
            (new_uuid, name, analysis_data)
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        # Re-raise the exception to be handled by the caller
        raise e
    finally:
        conn.close()
    return new_uuid

def get_analysis_by_uuid(analysis_uuid: str) -> sqlite3.Row:
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

def add_examples() -> list[str]:
    examples: list[str] = [
        os.path.join('static', 'json', 'usuário_da_ferramenta.json'),
        os.path.join('static', 'json', 'examples', 'a_aguia_e_a_raposa.json'),
        os.path.join('static', 'json', 'examples', 'a_gansa_dos_ovos_de_ouro.json'),
        os.path.join('static', 'json', 'examples', 'ladrao_e_o_cao_de_guarda.json'),
        os.path.join('static', 'json', 'examples', 'o_rato_do_campo_e_o_rato_da_cidade.json'),
    ]
    ids = []
    for e in examples:
        if os.path.exists(e):
            try:
                with open(e, 'r', encoding='utf-8') as f:
                   id = insert_analysis(e.split('\\')[-1].split('.')[0].replace('_', ' '), f.read())
                   ids.append(id)
            except Exception as e:
                print(f"Error loading example: {e}")
    return ids

if __name__ == '__main__':
    # This will initialize the database and table if the script is run directly
    init_db()
    print(f"Database '{DATABASE_NAME}' initialized and 'analyses' table created/verified.")

    # Example usage (optional, for testing)
    #try:
    print(add_examples())
    #    print("Examples added to database.")
    #    all_analyses = get_all_analyses()
    #    print(f"Total analyses: {len(all_analyses)}")
    #except sqlite3.Error as e:
    #    print(f"An error occurred: {e}")

    n = get_all_analyses()
    print([t['name'] for t in n])