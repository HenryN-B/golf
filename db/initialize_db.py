import sqlite3

def initialize_database():
    # Connect to SQLite database (creates the file if it doesn't exist)
    conn = sqlite3.connect("db/game.db")
    cursor = conn.cursor()

    # Read and execute schema.sql
    with open("db/schema.sql", "r") as schema_file:
        schema = schema_file.read()
        cursor.executescript(schema)

    # Commit and close connection
    conn.commit()
    conn.close()
    print("Database initialized successfully.")
    
    

if __name__ == "__main__":
    initialize_database()