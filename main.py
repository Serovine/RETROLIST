from database import init_db
import customtkinter as ctk
import sqlite3
import os
import subprocess
from tkinter import filedialog
import shutil
from PIL import Image

# Set initial theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RetroLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RETROLIST")
        self.geometry("800x600")
        
        # ให้มันเช็กและสร้าง DB ทันทีที่เปิดแอป (ถ้ามีอยู่แล้ว มันจะไม่ทำอะไร)
        init_db()
        
        # Show the home screen on startup
        self.show_home()

    def clear_screen(self):
        """Destroy all widgets to switch screens."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_home(self):
        """Master View: Show list of consoles."""
        self.clear_screen()
        
        # Top bar with Add button
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(top_frame, text="Console Manager", font=("Arial", 24, "bold")).pack(side="left")
        ctk.CTkButton(top_frame, text="➕ Add Console", width=120, fg_color="#28a745", hover_color="#218838", command=self.open_add_console).pack(side="right")

        # Fetch consoles
        conn = sqlite3.connect('retrolist.db')
        cursor = conn.cursor()
        # เพิ่มการดึง icon_path มาด้วย
        cursor.execute("SELECT id, name, icon_path FROM consoles")
        consoles = cursor.fetchall()
        conn.close()

        if not consoles:
            ctk.CTkLabel(self, text="No consoles found in database.").pack(pady=20)
            return

        for console in consoles:
            console_id = console[0]
            console_name = console[1]
            icon_path = console[2]
            
            row_frame = ctk.CTkFrame(self, fg_color="transparent")
            row_frame.pack(pady=10)

            # --- Render Icon ---
            if icon_path and os.path.exists(icon_path):
                try:
                    pil_image = Image.open(icon_path)
                    icon_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(50, 50))
                    lbl_icon = ctk.CTkLabel(row_frame, text="", image=icon_image, width=50, height=50)
                except:
                    lbl_icon = ctk.CTkLabel(row_frame, text="ERR", width=50, height=50, fg_color="#dc3545", corner_radius=5)
            else:
                lbl_icon = ctk.CTkLabel(row_frame, text="IMG", width=50, height=50, fg_color="#495057", text_color="white", corner_radius=5)
            
            lbl_icon.pack(side="left", padx=(0, 15))

            # --- Buttons ---
            btn_enter = ctk.CTkButton(
                row_frame, text=console_name, font=("Arial", 16), width=200, height=50,
                command=lambda cid=console_id, cname=console_name: self.show_library(cid, cname)
            )
            btn_enter.pack(side="left", padx=10)

            btn_setting = ctk.CTkButton(
                row_frame, text="⚙️ Settings", width=80, height=50, fg_color="#6c757d", hover_color="#5a6268",
                # ส่งแค่ ID กับ Name ก็พอแล้ว เพราะ Settings ไปดึงข้อมูลเอง
                command=lambda cid=console_id, cname=console_name: self.open_console_settings(cid, cname)
            )
            btn_setting.pack(side="left")
    
    def open_add_console(self):
        """Popup window to create a new console."""
        popup = ctk.CTkToplevel(self)
        popup.title("Add New Console")
        popup.geometry("400x150")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Console Name:", font=("Arial", 14)).pack(pady=(20, 5))
        entry_name = ctk.CTkEntry(popup, width=250)
        entry_name.pack()

        def save_new_console():
            new_name = entry_name.get().strip()
            if not new_name:
                return # ถ้าไม่พิมพ์อะไรเลย ให้ข้ามไป
                
            conn = sqlite3.connect('retrolist.db')
            c = conn.cursor()
            try:
                # สร้างเครื่องใหม่ โดยปล่อย Path ว่างไว้ก่อน ให้ผู้ใช้ไปกด Settings ทีหลัง
                c.execute("INSERT INTO consoles (name, emu_path, rom_path) VALUES (?, '', '')", (new_name,))
                conn.commit()
            except sqlite3.IntegrityError:
                print("Error: Console name already exists.")
            conn.close()
            
            popup.destroy()
            self.show_home() # โหลดหน้าแรกใหม่เพื่อโชว์ปุ่มเครื่องเกมที่เพิ่งสร้าง

        ctk.CTkButton(popup, text="Create", fg_color="#007bff", hover_color="#0056b3", command=save_new_console).pack(pady=20)

    def open_console_settings(self, console_id, console_name):
        """Popup window to configure emulator, rom paths, and console icon."""
        # 1. Fetch fresh data from DB
        conn = sqlite3.connect('retrolist.db')
        cursor = conn.cursor()
        cursor.execute("SELECT emu_path, rom_path, icon_path FROM consoles WHERE id = ?", (console_id,))
        row = cursor.fetchone()
        conn.close()

        current_emu, current_rom, current_icon = row if row else ("", "", "")

        popup = ctk.CTkToplevel(self)
        popup.title(f"Settings: {console_name}")
        popup.geometry("600x450") # ขยายความสูงเผื่อที่ให้ปุ่มอัปโหลดรูป
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

        self.temp_icon_path = None
        def browse_icon():
            path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
            if path:
                self.temp_icon_path = path
                lbl_icon_status.configure(text="Ready to save", text_color="#007bff")
        ctk.CTkButton(icon_frame, text="Browse Image", width=100, command=browse_icon).pack(side="right")

        # --- Save Logic ---
        def save_config():
            new_emu = emu_entry.get()
            new_rom = rom_entry.get()
            final_icon = current_icon
            
            # Copy image to icons folder if selected
            if self.temp_icon_path:
                os.makedirs("icons", exist_ok=True)
                ext = os.path.splitext(self.temp_icon_path)[1]
                target_path = os.path.join("icons", f"console_{console_id}{ext}")
                shutil.copy(self.temp_icon_path, target_path)
                final_icon = target_path

            conn = sqlite3.connect('retrolist.db')
            c = conn.cursor()
            c.execute("UPDATE consoles SET emu_path=?, rom_path=?, icon_path=? WHERE id=?", (new_emu, new_rom, final_icon, console_id))
            conn.commit()
            conn.close()
            
            popup.destroy()
            self.show_home() 

        ctk.CTkButton(popup, text="Save Config", fg_color="#28a745", hover_color="#218838", command=save_config).pack(pady=30)

    def show_library(self, console_id, console_name):
        """Detail View: Show ROMs for the selected console."""
        self.clear_screen()

        # Top bar (Navigation)
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=20)
        
        btn_back = ctk.CTkButton(top_frame, text="< Back", width=80, command=self.show_home)
        btn_back.pack(side="left")
        
        lbl_title = ctk.CTkLabel(top_frame, text=f"{console_name} Library", font=("Arial", 24, "bold"))
        lbl_title.pack(side="left", padx=20)

        btn_scan = ctk.CTkButton(
            top_frame, 
            text="🔄 Scan ROMs", 
            width=100, 
            fg_color="#007bff", 
            hover_color="#0056b3",
            command=lambda cid=console_id, cname=console_name: self.scan_roms(cid, cname)
        )
        btn_scan.pack(side="right", padx=20)

        # 1. Fetch EVERYTHING needed for the Card UI
        conn = sqlite3.connect('retrolist.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT roms.id, roms.game_name, roms.file_name, consoles.rom_path, 
                   roms.developer, roms.release_year, roms.genre, roms.cover_path
            FROM roms 
            JOIN consoles ON roms.console_id = consoles.id 
            WHERE roms.console_id = ?
        ''', (console_id,))
        roms = cursor.fetchall()
        conn.close()

        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        if not roms:
            ctk.CTkLabel(scroll_frame, text="No ROMs found in database.").pack(pady=20)
            return

        # 2. Render ROM row as a "Card"
        for rom in roms:
            rom_id = rom[0]
            game_name = rom[1]
            file_name = rom[2]
            rom_folder = rom[3]
            developer = rom[4]
            release_year = rom[5]
            genre = rom[6]
            cover_path = rom[7] # Will use this later for real images
            
            # Check file existence
            full_path = os.path.join(rom_folder, file_name) if rom_folder else ""
            is_exists = os.path.exists(full_path)
            
            # Card Frame (make it taller with padding)
            card_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
            card_frame.pack(fill="x", pady=8, ipady=10)

            # --- LEFT: Image Component ---
            # เช็กว่ามี Path รูปใน Database และไฟล์นั้นมีอยู่จริงในเครื่องหรือไม่
            if cover_path and os.path.exists(cover_path):
                try:
                    # เปิดรูปด้วย Pillow และนำเข้า CTkImage เพื่อปรับขนาด
                    pil_image = Image.open(cover_path)
                    cover_image = ctk.CTkImage(
                        light_image=pil_image, 
                        dark_image=pil_image, 
                        size=(134, 110) # ล็อกขนาดให้เท่ากรอบเดิมเป๊ะ
                    )
                    
                    img_label = ctk.CTkLabel(
                        card_frame, 
                        text="", # ลบข้อความออกเมื่อมีรูป
                        image=cover_image,
                        width=80, 
                        height=110,
                        corner_radius=5
                    )
                except Exception as e:
                    # กรณีไฟล์รูปเสียหรืออ่านไม่ได้
                    print(f"Error loading image {cover_path}: {e}")
                    img_label = ctk.CTkLabel(
                        card_frame, 
                        text="IMG\nERROR", 
                        width=80, height=110, 
                        fg_color="#dc3545", text_color="white", corner_radius=5
                    )
            else:
                # กรณีเกมนี้ยังไม่ได้อัปรูปลง Database
                img_label = ctk.CTkLabel(
                    card_frame, 
                    text="NO\nIMAGE", 
                    width=80, 
                    height=110, 
                    fg_color="#495057", 
                    text_color="white",
                    corner_radius=5
                )
                
            img_label.pack(side="left", padx=15, pady=10)

            # --- MIDDLE: Info Details ---
            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

            title_color = "white" if is_exists else "#ff4c4c"
            
            # Game Name (Bold)
            ctk.CTkLabel(info_frame, text=game_name, font=("Arial", 18, "bold"), text_color=title_color).pack(anchor="w")
            
            # File Name & Status
            status_text = "" if is_exists else " [FILE MISSING]"
            ctk.CTkLabel(info_frame, text=f"File: {file_name}{status_text}", font=("Arial", 12), text_color="gray" if is_exists else "#ff4c4c").pack(anchor="w", pady=(2, 10))
            
            # Metadata Row
            meta_text = f"Dev: {developer}   |   Year: {release_year}   |   Genre: {genre}"
            ctk.CTkLabel(info_frame, text=meta_text, font=("Arial", 13), text_color="#adb5bd").pack(anchor="w")

            # --- RIGHT: Action Buttons ---
            btn_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=20)
            
            btn_launch = ctk.CTkButton(
                btn_frame, 
                text="Launch" if is_exists else "Missing", 
                width=100, 
                fg_color="#28a745" if is_exists else "gray", 
                hover_color="#218838" if is_exists else "gray",
                state="normal" if is_exists else "disabled",
                command=lambda rid=rom_id, cid=console_id: self.trigger_launch(rid, cid)
            )
            btn_launch.pack(pady=(0, 5))

            btn_edit = ctk.CTkButton(
                btn_frame,
                text="📝 Edit",
                width=100,
                fg_color="#6c757d",
                hover_color="#5a6268",
                command=lambda rid=rom_id, cid=console_id, cname=console_name: self.open_rom_editor(rid, cid, cname)
            )
            btn_edit.pack(pady=(5, 0))

            btn_edit.pack(pady=(5, 0))

            # --- เพิ่มปุ่ม Delete ตรงนี้ ---
            btn_delete = ctk.CTkButton(
                btn_frame,
                text="🗑️ Delete",
                width=100,
                fg_color="#dc3545",
                hover_color="#c82333",
                # เปลี่ยนให้เรียก confirm_delete แทน
                command=lambda rid=rom_id, cid=console_id, gname=game_name: self.confirm_delete(rid, cid, console_name, gname)
            )
            btn_delete.pack(pady=(5, 0))
    
    def open_rom_editor(self, rom_id, console_id, console_name):
        """Popup window to edit ROM metadata and upload cover."""
        conn = sqlite3.connect('retrolist.db')
        cursor = conn.cursor()
        cursor.execute("SELECT game_name, developer, release_year, genre, file_name, cover_path FROM roms WHERE id = ?", (rom_id,))
        rom_data = cursor.fetchone()
        conn.close()

        if not rom_data:
            return

        current_name, current_dev, current_year, current_genre, file_name, current_cover = rom_data

        popup = ctk.CTkToplevel(self)
        popup.title(f"Edit Metadata: {file_name}")
        popup.geometry("500x550")
        popup.grab_set() 

        ctk.CTkLabel(popup, text="Game Metadata", font=("Arial", 20, "bold")).pack(pady=15)

        def create_input_row(parent, label_text, default_value):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(fill="x", padx=30, pady=5)
            ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(frame, width=250)
            entry.pack(side="left", fill="x", expand=True)
            if default_value and default_value != "Unknown":
                entry.insert(0, default_value)
            return entry

        entry_name = create_input_row(popup, "Game Name:", current_name)
        entry_dev = create_input_row(popup, "Developer:", current_dev)
        entry_year = create_input_row(popup, "Release Year:", current_year)
        entry_genre = create_input_row(popup, "Genre:", current_genre)

        # --- ส่วนจัดการรูปปก (Cover Upload UI) ---
        cover_frame = ctk.CTkFrame(popup, fg_color="transparent")
        cover_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(cover_frame, text="Cover Image:", width=120, anchor="w").pack(side="left")
        
        lbl_cover_status = ctk.CTkLabel(cover_frame, text="Present" if current_cover else "No Image", text_color="#28a745" if current_cover else "gray")
        lbl_cover_status.pack(side="left", padx=10)
        
        # ตัวแปรเก็บ Path รูปชั่วคราวเผื่อกด Browse
        self.temp_cover_path = None

        def browse_cover():
            path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
            if path:
                self.temp_cover_path = path
                lbl_cover_status.configure(text="Ready to save", text_color="#007bff")

        ctk.CTkButton(cover_frame, text="Browse Image", width=100, command=browse_cover).pack(side="right")

        def save_metadata():
            new_name = entry_name.get().strip() or os.path.splitext(file_name)[0]
            new_dev = entry_dev.get().strip() or "Unknown"
            new_year = entry_year.get().strip() or "Unknown"
            new_genre = entry_genre.get().strip() or "Unknown"
            
            final_cover_path = current_cover

            # ถ้ามีการเลือกรูปใหม่ ให้ทำการก๊อปปี้ไปไว้ในโฟลเดอร์ covers
            if self.temp_cover_path:
                os.makedirs("covers", exist_ok=True)
                ext = os.path.splitext(self.temp_cover_path)[1]
                # ตั้งชื่อไฟล์ตาม ID เกม เช่น covers/rom_1.jpg เพื่อกันชื่อซ้ำ
                target_path = os.path.join("covers", f"rom_{rom_id}{ext}")
                
                shutil.copy(self.temp_cover_path, target_path)
                final_cover_path = target_path

            conn = sqlite3.connect('retrolist.db')
            c = conn.cursor()
            c.execute('''
                UPDATE roms 
                SET game_name=?, developer=?, release_year=?, genre=?, cover_path=?
                WHERE id=?
            ''', (new_name, new_dev, new_year, new_genre, final_cover_path, rom_id))
            conn.commit()
            conn.close()

            print(f"Metadata saved. Cover Path: {final_cover_path}")
            popup.destroy()
            self.show_library(console_id, console_name)

        ctk.CTkButton(popup, text="💾 Save Changes", fg_color="#28a745", hover_color="#218838", command=save_metadata).pack(pady=20)

    def delete_rom(self, rom_id, console_id, console_name):
        """Delete ROM from database and refresh UI."""
        conn = sqlite3.connect('retrolist.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM roms WHERE id = ?", (rom_id,))
        conn.commit()
        conn.close()
        
        print(f"Deleted ROM ID: {rom_id} from database.")
        # โหลดหน้า UI ใหม่ให้ชื่อหายไป
        self.show_library(console_id, console_name)
    
    def confirm_delete(self, rom_id, console_id, console_name, game_name):
        """Popup window to confirm deletion before actually deleting."""
        popup = ctk.CTkToplevel(self)
        popup.title("Confirm Action")
        popup.geometry("350x150")
        popup.grab_set() # บล็อกไม่ให้ไปกดหน้าต่างหลักจนกว่าจะตอบคำถามนี้

        # ข้อความถามยืนยัน
        lbl_msg = ctk.CTkLabel(popup, text=f"Confirm to delete this game from library?\n[{game_name}]", font=("Arial", 14))
        lbl_msg.pack(pady=20)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10)

        # ลอจิกเมื่อกด Yes !
        def on_yes():
            popup.destroy() # ปิดหน้าต่างถาม
            self.delete_rom(rom_id, console_id, console_name) # เรียกฟังก์ชันลบของจริง

        # ลอจิกเมื่อกด Not yes !
        def on_no():
            popup.destroy() # ปิดหน้าต่างเฉยๆ ไม่ทำอะไร

        # ปุ่ม Yes ! (สีแดง) และ Not yes ! (สีเทา)
        ctk.CTkButton(btn_frame, text="Yes !", width=100, fg_color="#dc3545", hover_color="#c82333", command=on_yes).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Not yes !", width=100, fg_color="#6c757d", hover_color="#5a6268", command=on_no).pack(side="left", padx=10)

    def trigger_launch(self, rom_id, console_id):
        """Execute the emulator and pass the ROM file path."""
        # 1. เชื่อมต่อฐานข้อมูล
        conn = sqlite3.connect('retrolist.db')
        cursor = conn.cursor()
        
        # 2. ดึง Path ของ Emulator และ โฟลเดอร์เกมจากตาราง consoles
        cursor.execute("SELECT emu_path, rom_path FROM consoles WHERE id = ?", (console_id,))
        console_data = cursor.fetchone()
        
        # 3. ดึงชื่อไฟล์เกมจากตาราง roms
        cursor.execute("SELECT file_name FROM roms WHERE id = ?", (rom_id,))
        rom_data = cursor.fetchone()
        
        conn.close()

        # 4. ประกอบร่างและยิงคำสั่ง
        if console_data and rom_data:
            emu_exe = console_data[0]
            rom_folder = console_data[1]
            file_name = rom_data[0]
            
            # รวมโฟลเดอร์กับชื่อไฟล์เข้าด้วยกัน (เช่น C:/roms/sfc + mario.smc)
            full_rom_path = os.path.join(rom_folder, file_name)
            
            print(f"Executing: {emu_exe} \"{full_rom_path}\"")
            
            try:
                # สั่งรัน Emulator ผ่าน OS และปล่อยให้ทำงานแยกเป็นอิสระจาก Launcher
                subprocess.Popen([emu_exe, full_rom_path])
            except FileNotFoundError:
                print(f"Error: Not found Emulator at {emu_exe}")
            except Exception as e:
                print(f"Execution Error: {e}")
        else:
            print("Error: Not found Rom in database")
    
    def scan_roms(self, console_id, console_name):
        """Scan the ROM directory and update the database with new files."""
        conn = sqlite3.connect('retrolist.db')
        cursor = conn.cursor()
        
        # 1. Fetch current ROM path for this console
        cursor.execute("SELECT rom_path FROM consoles WHERE id = ?", (console_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            print(f"Error: No ROM path configured for {console_name}.")
            conn.close()
            return
            
        rom_folder = result[0]
        
        # 2. Check if the folder exists on the hard drive
        if not os.path.exists(rom_folder):
            print(f"Error: The folder '{rom_folder}' does not exist.")
            conn.close()
            return

        # 3. Scan directory and insert new ROMs
        added_count = 0
        for file in os.listdir(rom_folder):
            # You can add more extensions here if needed
            if file.lower().endswith(('.smc', '.sfc', '.zip', '.iso', '.bin', '.nes')):
                game_name = os.path.splitext(file)[0]
                
                # Check if this file is already in the database to prevent duplicates
                cursor.execute("SELECT id FROM roms WHERE console_id = ? AND file_name = ?", (console_id, file))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO roms (console_id, file_name, game_name, cover_path, developer, release_year, genre)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (console_id, file, game_name, "", "Unknown", "Unknown", "Unknown"))
                    added_count += 1

        conn.commit()
        conn.close()
        print(f"Scan complete: Added {added_count} new games to {console_name}.")
        
        # 4. Refresh the library page to show new games
        self.show_library(console_id, console_name)

if __name__ == "__main__":
    app = RetroLauncher()
    app.mainloop()
