import sqlite3

def clear_database():
    conn = sqlite3.connect('db/game.db')
    conn.row_factory = sqlite3.Row

    try:
        with conn:
            conn.execute('DELETE FROM rooms')
            conn.execute('DELETE FROM player')
            conn.execute('DELETE FROM games')
            conn.execute('DELETE FROM player_cards')
            conn.execute('DELETE FROM deck')
            conn.execute('DELETE FROM discard')
        with conn:
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'player'")
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'player_cards'")
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'deck'")
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'discard'")
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'games'")
    finally:
        conn.close()
        
if __name__ == "__main__":
    clear_database()