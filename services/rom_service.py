import os
import subprocess
import csv
from database import get_connection

def get_rom_count(console_id, search_term="", genre_filter="All"):
    """Fetch total number of ROMs matching the current filter (for pagination)."""
    conn = get_connection()
    cursor = conn.cursor()
    query = '''
        SELECT COUNT(id) FROM roms 
        WHERE console_id = ? 
          AND game_name LIKE '%' || ? || '%' 
          AND (? = 'All' OR genre = ?)
    '''
    cursor.execute(query, (console_id, search_term, genre_filter, genre_filter))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_roms_for_console(console_id, sort_by="Added (Newest)", search_term="", genre_filter="All", limit=20, offset=0):
    """Fetch ROMs with sorting, filtering, and pagination limit/offset."""
    conn = get_connection()
    cursor = conn.cursor()
    
    order_clause = "ORDER BY roms.id DESC" 
    if sort_by == "Added (Oldest)": order_clause = "ORDER BY roms.id ASC"
    elif sort_by == "Name (A-Z)": order_clause = "ORDER BY roms.game_name ASC"
    elif sort_by == "Name (Z-A)": order_clause = "ORDER BY roms.game_name DESC"
    elif sort_by == "Year (New-Old)": order_clause = "ORDER BY roms.release_year DESC"
    elif sort_by == "Year (Old-New)": order_clause = "ORDER BY roms.release_year ASC"
    elif sort_by == "Genre": order_clause = "ORDER BY roms.genre ASC, roms.game_name ASC"

    # จัดการ LIMIT และ OFFSET
    limit_clause = ""
    params = [console_id, search_term, genre_filter, genre_filter]
    
    if limit != "All":
        limit_clause = "LIMIT ? OFFSET ?"
        params.extend([int(limit), int(offset)])

    query = f'''
        SELECT roms.id, roms.game_name, roms.file_name, consoles.rom_path, 
               roms.developer, roms.release_year, roms.genre, roms.cover_path,
               consoles.emu_path, roms.language, roms.is_hack, roms.is_translated
        FROM roms 
        JOIN consoles ON roms.console_id = consoles.id 
        WHERE roms.console_id = ?
          AND roms.game_name LIKE '%' || ? || '%' 
          AND (? = 'All' OR roms.genre = ?)
        {order_clause}
        {limit_clause}
    '''
    
    cursor.execute(query, tuple(params))
    roms_data = cursor.fetchall()
    conn.close()

    processed_roms = []
    for row in roms_data:
        rom_id, game_name, file_name, rom_folder, developer, release_year, genre, cover_path, emu_path, language, is_hack, is_translated = row
        full_rom_path = os.path.join(rom_folder, file_name) if rom_folder else ""
        is_exists = os.path.exists(full_rom_path)
        processed_roms.append({
            'rom_id': rom_id, 
            'game_name': game_name, 
            'file_name': file_name, 
            'full_rom_path': full_rom_path, 
            'developer': developer, 
            'release_year': release_year, 
            'genre': genre, 
            'cover_path': cover_path, 
            'emu_path': emu_path, 
            'is_exists': is_exists,
            'language': language, 
            'is_hack': is_hack, 
            'is_translated': is_translated
        })
        
    return processed_roms

def get_genres_for_console(console_id):
    """Fetch all unique genres available in the database for a specific console."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT genre FROM roms WHERE console_id = ? AND genre != 'Unknown' AND genre != ''", (console_id,))
    genres = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ["All"] + sorted(genres)

def launch_game(emu_path, rom_path):
    """Execute the emulator with the ROM path."""
    if not emu_path or not rom_path:
        print("Error: Missing Emulator or ROM path.")
        return
        
    print(f"Executing: {emu_path} \"{rom_path}\"")
    try:
        subprocess.Popen([emu_path, rom_path])
    except FileNotFoundError:
        print(f"Error: Emulator not found at {emu_path}")
    except Exception as e:
        print(f"Execution Error: {e}")

def scan_and_add_roms(console_id):
    """Scan the ROM directory and insert new files into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT rom_path FROM consoles WHERE id = ?", (console_id,))
    result = cursor.fetchone()

    if not result or not result[0]:
        conn.close()
        return -1 # No path configured

    rom_folder = result[0]
    if not os.path.exists(rom_folder):
        conn.close()
        return -2 # Folder not found

    added_count = 0
    valid_extensions = ('.smc', '.sfc', '.zip', '.iso', '.bin', '.nes', '.gba', '.gbc', '.gb', '.md', '.z64', '.n64', '.v64')

    for file in os.listdir(rom_folder):
        if file.lower().endswith(valid_extensions):
            game_name = os.path.splitext(file)[0]
            cursor.execute("SELECT id FROM roms WHERE console_id = ? AND file_name = ?", (console_id, file))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO roms (
                        console_id, file_name, game_name, cover_path, 
                        developer, release_year, genre, language, is_hack, is_translated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (console_id, file, game_name, "", "Unknown", "Unknown", "Unknown", "Unknown", 0, 0))
                added_count += 1

    conn.commit()
    conn.close()
    return added_count

def delete_rom(rom_id):
    """Delete a specific ROM from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM roms WHERE id = ?", (rom_id,))
    conn.commit()
    conn.close()

def update_rom_metadata(rom_id, game_name, developer, release_year, genre, language, is_hack, is_translated, cover_path):
    """Update ROM metadata in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE roms 
        SET game_name=?, developer=?, release_year=?, genre=?, language=?, is_hack=?, is_translated=?, cover_path=?
        WHERE id=?
    ''', (game_name, developer, release_year, genre, language, is_hack, is_translated, cover_path, rom_id))
    conn.commit()
    conn.close()

def export_roms_to_csv(filepath):
    """Export ROMs metadata to a CSV file."""
    conn = get_connection()
    cursor = conn.cursor()
    # ดึงข้อมูลมาเฉพาะที่จำเป็นต้องแก้ (ไม่เอา path ไฟล์รูป หรือ path เครื่อง emu ออกมาให้รก)
    cursor.execute('''
        SELECT r.id, c.name as console_name, r.file_name, r.game_name, 
               r.developer, r.release_year, r.genre, r.language, 
               r.is_hack, r.is_translated
        FROM roms r
        LEFT JOIN consoles c ON r.console_id = c.id
    ''')
    rows = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]

    # ใช้ utf-8-sig เพื่อป้องกันปัญหา Font ภาษาต่างดาวเวลาเปิดใน Excel
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    conn.close()

def import_metadata_from_csv(filepath):
    """Import and update ROMs metadata from a CSV file using 'id' as key."""
    conn = get_connection()
    cursor = conn.cursor()
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # เช็กว่ามีคอลัมน์ id ไหม ถ้าไม่มี หรือถูกลบทิ้งไป ให้ข้าม
            if 'id' not in row or not row['id']:
                continue
                
            cursor.execute('''
                UPDATE roms
                SET game_name=?, developer=?, release_year=?, genre=?, language=?, is_hack=?, is_translated=?
                WHERE id=?
            ''', (
                row.get('game_name', ''),
                row.get('developer', ''),
                row.get('release_year', ''),
                row.get('genre', ''),
                row.get('language', ''),
                int(row.get('is_hack', 0) or 0),
                int(row.get('is_translated', 0) or 0),
                row['id']
            ))
    conn.commit()
    conn.close()