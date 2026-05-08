from database import get_connection

def get_all_consoles():
    """Fetch all consoles and total ROM count, sorted by user preference."""
    conn = get_connection()
    cursor = conn.cursor()
    # ดึงข้อมูลและเรียงลำดับตาม sort_order ก่อน ถ้าเท่ากันค่อยเรียงตาม id
    cursor.execute('''
        SELECT c.id, c.name, c.icon_path, 
               (SELECT COUNT(id) FROM roms WHERE console_id = c.id) as rom_count
        FROM consoles c
        ORDER BY c.sort_order ASC, c.id ASC
    ''')
    consoles = cursor.fetchall()
    conn.close()
    return consoles

def update_console_orders(order_list):
    """Bulk update the sort_order for consoles.
       order_list is a list of tuples: [(console_id, new_sort_order), ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("UPDATE consoles SET sort_order = ? WHERE id = ?", [(order, cid) for cid, order in order_list])
    conn.commit()
    conn.close()

def add_console(name):
    """Insert a new console into the database."""
    if not name:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO consoles (name, emu_path, rom_path) VALUES (?, '', '')", (name,))
        conn.commit()
        success = True
    except:
        success = False # Name already exists
    conn.close()
    return success

def get_console_by_id(console_id):
    """Fetch specific console settings by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT emu_path, rom_path, icon_path FROM consoles WHERE id = ?", (console_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_console_settings(console_id, emu_path, rom_path, icon_path):
    """Update emulator, rom, and icon paths for a console."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE consoles SET emu_path=?, rom_path=?, icon_path=? WHERE id=?", 
                   (emu_path, rom_path, icon_path, console_id))
    conn.commit()
    conn.close()

def delete_console(console_id):
    """Delete a console and all its associated ROMs (via CASCADE) from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    # เนื่องจากเราตั้ง ON DELETE CASCADE ไว้ ลบแค่ console ข้อมูล roms จะหายไปเอง
    cursor.execute("DELETE FROM consoles WHERE id = ?", (console_id,))
    conn.commit()
    conn.close()