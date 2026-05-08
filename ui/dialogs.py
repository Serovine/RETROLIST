import customtkinter as ctk
import os
import shutil
from PIL import Image
from tkinter import filedialog
from services.console_service import add_console, get_console_by_id, update_console_settings, get_all_consoles, update_console_orders, delete_console
from services.rom_service import delete_rom, update_rom_metadata

# ==========================================
# 1. Add Console Dialog
# ==========================================
def open_add_console_dialog(parent, refresh_callback):
    """Popup window to create a new console."""
    popup = ctk.CTkToplevel(parent)
    popup.title("Add New Console")
    popup.geometry("400x150")
    popup.grab_set()

    ctk.CTkLabel(popup, text="Console Name:", font=("Arial", 14)).pack(pady=(20, 5))
    entry_name = ctk.CTkEntry(popup, width=250)
    entry_name.pack()

    def save_new_console():
        new_name = entry_name.get().strip()
        if new_name:
            success = add_console(new_name)
            if not success:
                print(f"Error: Console '{new_name}' might already exist.")
        
        popup.destroy()
        refresh_callback()

    ctk.CTkButton(popup, text="Create", fg_color="#007bff", hover_color="#0056b3", command=save_new_console).pack(pady=20)


# ==========================================
# 2. Confirm Delete ROM Dialog
# ==========================================
def open_confirm_delete_dialog(parent, rom_id, game_name, refresh_callback):
    """Popup window to confirm ROM deletion."""
    popup = ctk.CTkToplevel(parent)
    popup.title("Confirm Delete")
    popup.geometry("350x150")
    popup.grab_set()

    ctk.CTkLabel(popup, text=f"Delete '{game_name}'?", font=("Arial", 14, "bold")).pack(pady=(20, 10))

    btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
    btn_frame.pack(pady=10)

    def on_yes():
        delete_rom(rom_id)  # <--- ตัวแปรสำคัญ สั่งลบจาก Database จริงๆ
        popup.destroy()     # ปิดหน้าต่าง Popup
        refresh_callback()  # สั่งหน้า Library ให้รีเฟรชตัวเอง

    ctk.CTkButton(btn_frame, text="Yes", width=80, fg_color="#dc3545", hover_color="#c82333", command=on_yes).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="No", width=80, fg_color="#6c757d", hover_color="#5a6268", command=popup.destroy).pack(side="left", padx=10)


# ==========================================
# 3. Edit ROM Metadata Dialog
# ==========================================
# ตัวแปรช่วยเก็บ Path รูปชั่วคราว นอกฟังก์ชัน
temp_cover_path = None

def open_edit_rom_dialog(parent, rom_data, save_callback):
    """
    Popup window to edit ROM metadata.
    rom_data: dict containing current metadata
    save_callback: function to call when saving
    """
    global temp_cover_path
    temp_cover_path = None

    popup = ctk.CTkToplevel(parent)
    popup.title(f"Edit Metadata: {rom_data.get('file_name', '')}")
    popup.geometry("500x650") 
    popup.grab_set()

    ctk.CTkLabel(popup, text="Game Metadata", font=("Arial", 20, "bold")).pack(pady=15)

    def create_input_row(parent_frame, label_text, default_value):
        frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        frame.pack(fill="x", padx=30, pady=5)
        ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, width=250)
        entry.pack(side="left", fill="x", expand=True)
        if default_value and default_value != "Unknown":
            entry.insert(0, str(default_value))
        return entry

    # Basic Info
    entry_name = create_input_row(popup, "Game Name:", rom_data.get('game_name', ''))
    entry_dev = create_input_row(popup, "Developer:", rom_data.get('developer', ''))
    entry_year = create_input_row(popup, "Release Year:", rom_data.get('release_year', ''))
    entry_genre = create_input_row(popup, "Genre:", rom_data.get('genre', ''))
    lang_frame = ctk.CTkFrame(popup, fg_color="transparent")
    lang_frame.pack(fill="x", padx=30, pady=5)

    ctk.CTkLabel(lang_frame, text="Language:", width=120, anchor="w").pack(side="left")
    lang_var = ctk.StringVar(value=rom_data.get('language', 'Unknown'))
    lang_dropdown = ctk.CTkOptionMenu(lang_frame, variable=lang_var, values=["Unknown", "JP", "USA", "EU", "TH","RUS","ETC"])
    lang_dropdown.pack(side="left")

    check_frame = ctk.CTkFrame(popup, fg_color="transparent")
    check_frame.pack(fill="x", padx=30, pady=10)
    
    hack_var = ctk.IntVar(value=rom_data.get('is_hack', 0))
    trans_var = ctk.IntVar(value=rom_data.get('is_translated', 0))
    
    ctk.CTkCheckBox(check_frame, text="Hack ROM", variable=hack_var).pack(side="left", padx=(120, 20))
    ctk.CTkCheckBox(check_frame, text="Translated", variable=trans_var).pack(side="left")

    # --- Cover Upload ---
    cover_frame = ctk.CTkFrame(popup, fg_color="transparent")
    cover_frame.pack(fill="x", padx=30, pady=10)
    ctk.CTkLabel(cover_frame, text="Cover Image:", width=120, anchor="w").pack(side="left")
    
    current_cover = rom_data.get('cover_path', '')
    lbl_cover_status = ctk.CTkLabel(cover_frame, text="Present" if current_cover else "No Image", text_color="#28a745" if current_cover else "gray")
    lbl_cover_status.pack(side="left", padx=10)

    def browse_cover():
        global temp_cover_path
        path = filedialog.askopenfilename(filetypes=[("Image Files ", "*.png *.jpg *.jpeg")])
        if path:
            temp_cover_path = path
            lbl_cover_status.configure(text="Ready to save", text_color="#007bff")

    ctk.CTkButton(cover_frame, text="Browse Image", width=100, command=browse_cover).pack(side="right")

    # --- Save Logic ---
    def save_metadata():
        global temp_cover_path
        
        # ป้องกันบั๊ก Key Error: ดึง ID ให้ถูกไม่ว่าฐานข้อมูลจะส่งชื่อคอลัมน์มาเป็น id หรือ rom_id
        target_id = rom_data.get('id') or rom_data.get('rom_id')

        # Prepare data
        game_name = entry_name.get().strip() or os.path.splitext(rom_data.get('file_name', ''))[0]
        developer = entry_dev.get().strip() or "Unknown"
        release_year = entry_year.get().strip() or "Unknown"
        genre = entry_genre.get().strip() or "Unknown"
        language = lang_var.get()
        is_hack = hack_var.get()
        is_translated = trans_var.get()
        final_cover_path = rom_data.get('cover_path', '')

        # Process image copy if a new one was selected
        if temp_cover_path:
            os.makedirs("covers", exist_ok=True)
            target_path = os.path.join("covers", f"rom_{target_id}.jpg")
            
            try:
                with Image.open(temp_cover_path) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img = img.resize((160, 120), Image.Resampling.LANCZOS)
                    img.save(target_path, "JPEG", quality=85)
            except Exception as e:
                print(f"Error resizing image: {e}")
                import shutil
                shutil.copy(temp_cover_path, target_path)

            final_cover_path = target_path

        # --- อัปเดตลง Database ตรงนี้เลย ---
        if target_id:
            update_rom_metadata(
                rom_id=target_id,
                game_name=game_name,
                developer=developer,
                release_year=release_year,
                genre=genre,
                language=language,
                is_hack=is_hack,
                is_translated=is_translated,
                cover_path=final_cover_path
            )

        # โทรกลับไปสั่งให้ LibraryView รีเฟรชหน้าจอ (ไม่ต้องส่งข้อมูลไปให้มันแล้ว)
        save_callback()
        popup.destroy()

    ctk.CTkButton(popup, text="💾 Save Changes", fg_color="#28a745", hover_color="#218838", command=save_metadata).pack(pady=20)

# ==========================================
# 4. Console Settings Dialog
# ==========================================
temp_icon_path = None

def open_console_settings_dialog(parent, console_id, console_name, refresh_callback):
    """Popup window to configure emulator, rom paths, and console icon."""
    global temp_icon_path
    temp_icon_path = None

    row = get_console_by_id(console_id)
    current_emu, current_rom, current_icon = row if row else ("", "", "")

    popup = ctk.CTkToplevel(parent)
    popup.title(f"Settings: {console_name}")
    popup.geometry("600x450")
    popup.grab_set()

    # --- Emu Path UI ---
    ctk.CTkLabel(popup, text="Emulator Path (.exe):").pack(anchor="w", padx=20, pady=(20, 0))
    emu_frame = ctk.CTkFrame(popup, fg_color="transparent")
    emu_frame.pack(fill="x", padx=20, pady=5)
    emu_entry = ctk.CTkEntry(emu_frame)
    emu_entry.pack(side="left", fill="x", expand=True)
    if current_emu: emu_entry.insert(0, current_emu)
    
    def browse_emu():
        path = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
        if path:
            emu_entry.delete(0, 'end')
            emu_entry.insert(0, path)
            
    ctk.CTkButton(emu_frame, text="Browse", width=80, command=browse_emu).pack(side="right", padx=(10, 0))

    # --- Rom Path UI ---
    ctk.CTkLabel(popup, text="ROMs Folder Path:").pack(anchor="w", padx=20, pady=(10, 0))
    rom_frame = ctk.CTkFrame(popup, fg_color="transparent")
    rom_frame.pack(fill="x", padx=20, pady=5)
    rom_entry = ctk.CTkEntry(rom_frame)
    rom_entry.pack(side="left", fill="x", expand=True)
    if current_rom: rom_entry.insert(0, current_rom)
    
    def browse_rom():
        path = filedialog.askdirectory()
        if path:
            rom_entry.delete(0, 'end')
            rom_entry.insert(0, path)
            
    ctk.CTkButton(rom_frame, text="Browse", width=80, command=browse_rom).pack(side="right", padx=(10, 0))

    # --- Console Icon UI ---
    ctk.CTkLabel(popup, text="Console Icon Image:").pack(anchor="w", padx=20, pady=(10, 0))
    icon_frame = ctk.CTkFrame(popup, fg_color="transparent")
    icon_frame.pack(fill="x", padx=20, pady=5)
    lbl_icon_status = ctk.CTkLabel(icon_frame, text="Present" if current_icon else "No Icon", text_color="#28a745" if current_icon else "gray")
    lbl_icon_status.pack(side="left")

    def browse_icon():
        global temp_icon_path
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if path:
            temp_icon_path = path
            lbl_icon_status.configure(text="Ready to save", text_color="#007bff")
            
    ctk.CTkButton(icon_frame, text="Browse Image", width=100, command=browse_icon).pack(side="right")

    # --- Action Buttons (Save & Delete) ---
    btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
    btn_frame.pack(pady=30)

    def save_config():
        global temp_icon_path
        new_emu = emu_entry.get()
        new_rom = rom_entry.get()
        final_icon = current_icon
        
        if temp_icon_path:
            os.makedirs("icons", exist_ok=True)
            ext = os.path.splitext(temp_icon_path)[1]
            target_path = os.path.join("icons", f"console_{console_id}{ext}")
            shutil.copy(temp_icon_path, target_path)
            final_icon = target_path

        update_console_settings(console_id, new_emu, new_rom, final_icon)
        popup.destroy()
        refresh_callback() 

    def on_delete_clicked():
        popup.destroy() 
        open_confirm_delete_console_dialog(parent, console_id, console_name, refresh_callback)

    ctk.CTkButton(btn_frame, text="Save Config", fg_color="#28a745", hover_color="#218838", command=save_config).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="Delete Console", fg_color="#dc3545", hover_color="#c82333", command=on_delete_clicked).pack(side="left", padx=10)

# ==========================================
# 5. About Dialog (ตัวที่ทำให้เกิด ImportError)
# ==========================================
def open_about_dialog(parent):
    """Popup window showing software information."""
    popup = ctk.CTkToplevel(parent)
    popup.title("About")
    popup.geometry("400x220")
    popup.grab_set()

    # ข้อความเวอร์ชัน
    ctk.CTkLabel(popup, text="RetroList", font=("Arial", 28, "bold")).pack(pady=(30, 5))
    ctk.CTkLabel(popup, text="Software Version 0.001alpha", font=("Arial", 14, "bold")).pack()
    ctk.CTkLabel(popup, text="by Anonymous Zen 2026", font=("Arial", 12)).pack(pady=(5, 10))
    
    ctk.CTkButton(popup, text="Close", width=100, command=popup.destroy).pack(pady=10)

# ==========================================
# 6. Reorder Consoles Dialog
# ==========================================
def open_reorder_consoles_dialog(parent, refresh_callback):
    """Popup window to reorder consoles using Up/Down buttons."""
    popup = ctk.CTkToplevel(parent)
    popup.title("Reorder Consoles")
    popup.geometry("350x450")
    popup.grab_set()

    # ดึงข้อมูลคอนโซลมาเก็บเป็น List of Dicts เพื่อให้สลับตำแหน่งง่าย
    consoles = get_all_consoles()
    current_order = [{'id': c[0], 'name': c[1]} for c in consoles]

    ctk.CTkLabel(popup, text="Sort Consoles", font=("Arial", 20, "bold")).pack(pady=(15, 5))
    ctk.CTkLabel(popup, text="Use arrows to change the order").pack(pady=(0, 10))

    # กล่องแสดงรายชื่อ
    list_frame = ctk.CTkScrollableFrame(popup, fg_color="transparent")
    list_frame.pack(fill="both", expand=True, padx=20, pady=5)

    def render_list():
        # ล้างรายชื่อเก่าก่อนวาดใหม่
        for w in list_frame.winfo_children():
            w.destroy()
            
        for i, item in enumerate(current_order):
            row = ctk.CTkFrame(list_frame, corner_radius=5)
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"{i+1}. {item['name']}", font=("Arial", 14)).pack(side="left", padx=10, pady=5)

            # ปุ่มลูกศรลง
            btn_down = ctk.CTkButton(row, text="▼", width=30, fg_color="#6c757d", command=lambda idx=i: move_down(idx))
            btn_down.pack(side="right", padx=(2, 5), pady=5)
            # ปุ่มลูกศรขึ้น
            btn_up = ctk.CTkButton(row, text="▲", width=30, fg_color="#6c757d", command=lambda idx=i: move_up(idx))
            btn_up.pack(side="right", padx=2, pady=5)

            # ปิดการกดปุ่มขึ้นสำหรับอันแรกสุด และปุ่มลงสำหรับอันท้ายสุด
            if i == 0: btn_up.configure(state="disabled", fg_color="#495057")
            if i == len(current_order) - 1: btn_down.configure(state="disabled", fg_color="#495057")

    def move_up(idx):
        if idx > 0:
            current_order[idx], current_order[idx-1] = current_order[idx-1], current_order[idx]
            render_list()

    def move_down(idx):
        if idx < len(current_order) - 1:
            current_order[idx], current_order[idx+1] = current_order[idx+1], current_order[idx]
            render_list()

    def save_order():
        # แปลงข้อมูลกลับไปส่งให้ Service บันทึก (เอา ID มาจับคู่กับลำดับ Index)
        order_data = [(item['id'], idx) for idx, item in enumerate(current_order)]
        update_console_orders(order_data)
        popup.destroy()
        refresh_callback() # สั่งรีเฟรชหน้า Home

    ctk.CTkButton(popup, text="💾 Save Order", fg_color="#007bff", command=save_order).pack(pady=15)
    
    render_list() # วาดรายชื่อครั้งแรก

# ==========================================
# 7. Confirm Delete Console Dialog
# ==========================================
def open_confirm_delete_console_dialog(parent, console_id, console_name, refresh_callback):
    """Popup window to confirm console deletion."""
    popup = ctk.CTkToplevel(parent)
    popup.title("WARNING: Delete Console")
    popup.geometry("400x200")
    popup.grab_set()

    ctk.CTkLabel(popup, text="⚠️ DANGER ZONE ⚠️", font=("Arial", 18, "bold"), text_color="#dc3545").pack(pady=(20, 5))
    ctk.CTkLabel(popup, text=f"Are you sure you want to delete\n[{console_name}] ?", font=("Arial", 14)).pack()
    ctk.CTkLabel(popup, text="(This will clear all its ROMs from the database.\nYour actual game files will NOT be deleted.)", font=("Arial", 11), text_color="gray").pack(pady=5)

    btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
    btn_frame.pack(pady=15)

    def on_yes():
        delete_console(console_id)
        popup.destroy()
        refresh_callback()

    def on_no():
        popup.destroy()

    ctk.CTkButton(btn_frame, text="Yes, Delete It!", width=120, fg_color="#dc3545", hover_color="#c82333", command=on_yes).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="Cancel", width=120, fg_color="#6c757d", hover_color="#5a6268", command=on_no).pack(side="left", padx=10)