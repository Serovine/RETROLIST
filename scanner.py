import os
import sqlite3

def add_mock_console():
    """A function that simulates adding game console data to a database"""
    conn = sqlite3.connect('retrolist.db')
    c = conn.cursor()
    
    # Enter the virtual machine information (change the path to match your virtual folder)
    try:
        c.execute('''
            INSERT INTO consoles (name, icon_path, emu_path, rom_path) 
            VALUES ('Super Famicom', '', 'C:/Retrolist/emu/snes/snes9x.exe', 'C:/Retrolist/roms/sfc')
        ''')
        conn.commit()
        print("add 'Super Famicom' to database")
    except sqlite3.IntegrityError:
        print("console 'Super Famicom' already in database")
    conn.close()

def scan_roms_to_db(console_name):
    """scan foloder roms to database"""
    conn = sqlite3.connect('retrolist.db')
    c = conn.cursor()
    
    # 1. get ID and rom_path from console
    c.execute("SELECT id, rom_path FROM consoles WHERE name = ?", (console_name,))
    console = c.fetchone()
    
    if not console:
        print("not found this console in database")
        return
        
    console_id, rom_folder = console[0], console[1]
    
    # 2. check folder status
    if not os.path.exists(rom_folder):
        print(f"Error: not found {rom_folder}\n(Please create folder first)")
        return

    # 3. Scan file list
    added_count = 0
    for file in os.listdir(rom_folder):
        # กรองเฉพาะนามสกุลไฟล์เกม (คุณสามารถเพิ่มนามสกุลที่ต้องการได้ที่นี่)
        if file.lower().endswith(('.smc', '.sfc', '.zip', '.iso', '.bin')):
            game_name = os.path.splitext(file)[0] # ตัดนามสกุลออก เอามาตั้งเป็นชื่อเกมโชว์ชั่วคราว
            
            # 4. เช็คว่าไฟล์นี้เคยถูกแอดลง DB หรือยัง จะได้ไม่เบิ้ลซ้ำ
            c.execute("SELECT id FROM roms WHERE console_id = ? AND file_name = ?", (console_id, file))
            if not c.fetchone():
                c.execute('''
                    INSERT INTO roms (console_id, file_name, game_name, cover_path, developer, release_year, genre)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (console_id, file, game_name, "", "Unknown", "Unknown", "Unknown"))
                added_count += 1
                
    conn.commit()
    conn.close()
    print(f"Scan Complete: Found and Add New Game {added_count} to database")

if __name__ == "__main__":
    # ขั้นตอนการรันทดสอบ
    add_mock_console()
    scan_roms_to_db('Super Famicom')