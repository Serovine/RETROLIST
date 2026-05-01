import sqlite3

def init_db():
    # สร้างหรือเชื่อมต่อกับไฟล์ฐานข้อมูล retrolist.db
    conn = sqlite3.connect('retrolist.db')
    cursor = conn.cursor()

    # บังคับเปิดใช้งาน Foreign Key ของ SQLite (สำคัญมาก)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. ตารางเครื่องเกม (Consoles)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consoles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,      -- ชื่อเครื่องเกม
            icon_path TEXT,                 -- รูปประกอบเครื่อง
            emu_path TEXT NOT NULL,         -- emu path (.exe)
            rom_path TEXT NOT NULL          -- rom path (โฟลเดอร์เก็บเกม)
        )
    ''')

    # 2. ตารางเกม (Roms)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            console_id INTEGER NOT NULL,    -- ตัวเชื่อมว่าเกมนี้ของเครื่องไหน
            file_name TEXT NOT NULL,        -- ชื่อไฟล์เกม (.smc, .iso)
            game_name TEXT NOT NULL,        -- ชื่อเกม (เอาไว้โชว์สวยๆ)
            cover_path TEXT,                -- รูปปกเกม
            developer TEXT,                 -- ค่ายเกม
            release_year TEXT,              -- ปีที่ออก
            genre TEXT,                     -- แนวเกม
            FOREIGN KEY (console_id) REFERENCES consoles (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("Database 'retrolist.db' has been initialized successfully!")

# ทำให้ไฟล์นี้รันตัวเองได้เพื่อทดสอบสร้าง DB
if __name__ == "__main__":
    init_db()