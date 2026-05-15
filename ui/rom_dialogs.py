import customtkinter as ctk
import os
import shutil
from PIL import Image
from tkinter import filedialog
from services.rom_service import delete_rom, update_rom_metadata

# ==========================================
# 1. Confirm Delete ROM Dialog
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
        delete_rom(rom_id)  
        popup.destroy()     
        refresh_callback()  

    ctk.CTkButton(btn_frame, text="Yes", width=80, fg_color="#dc3545", hover_color="#c82333", command=on_yes).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="No", width=80, fg_color="#6c757d", hover_color="#5a6268", command=popup.destroy).pack(side="left", padx=10)

# ==========================================
# 2. Edit ROM Metadata Dialog
# ==========================================
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
        
        target_id = rom_data.get('id') or rom_data.get('rom_id')

        game_name = entry_name.get().strip() or os.path.splitext(rom_data.get('file_name', ''))[0]
        developer = entry_dev.get().strip() or "Unknown"
        release_year = entry_year.get().strip() or "Unknown"
        genre = entry_genre.get().strip() or "Unknown"
        language = lang_var.get()
        is_hack = hack_var.get()
        is_translated = trans_var.get()
        final_cover_path = rom_data.get('cover_path', '')

        if temp_cover_path:
            os.makedirs("covers", exist_ok=True)
            target_path = os.path.join("covers", f"rom_{target_id}.jpg")
            
            try:
                with Image.open(temp_cover_path) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img = img.resize((480, 360), Image.Resampling.LANCZOS)
                    img.save(target_path, "JPEG", quality=85)
            except Exception as e:
                print(f"Error resizing image: {e}")
                shutil.copy(temp_cover_path, target_path)

            final_cover_path = target_path

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

        save_callback()
        popup.destroy()

    ctk.CTkButton(popup, text="💾 Save Changes", fg_color="#28a745", hover_color="#218838", command=save_metadata).pack(pady=20)