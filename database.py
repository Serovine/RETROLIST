import sqlite3
import os

DB_PATH = 'retrolist.db'

def get_connection():
    """Returns a database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database schema with the latest table structures."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create consoles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consoles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            emu_path TEXT,
            rom_path TEXT,
            icon_path TEXT
        )
    ''')
    
    # Create roms table with new columns (language, is_hack, is_translated)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            console_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            game_name TEXT NOT NULL,
            cover_path TEXT,
            developer TEXT DEFAULT 'Unknown',
            release_year TEXT DEFAULT 'Unknown',
            genre TEXT DEFAULT 'Unknown',
            language TEXT DEFAULT 'Unknown',
            is_hack INTEGER DEFAULT 0,
            is_translated INTEGER DEFAULT 0,
            FOREIGN KEY (console_id) REFERENCES consoles (id) ON DELETE CASCADE
        )
    ''')
    
    # Create index for faster searching
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_console_id ON roms (console_id);')

    # Database Migration สำหรับ consoles
    try:
        cursor.execute("ALTER TABLE consoles ADD COLUMN sort_order INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # ถ้ามีคอลัมน์นี้อยู่แล้วให้ข้ามไป
    
    conn.commit()
    conn.close()
    print("Database initialized successfully with the new schema.")

# Allow running this file directly to generate the database
if __name__ == "__main__":
    init_db()