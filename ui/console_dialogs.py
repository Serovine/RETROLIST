import customtkinter as ctk
import os
import shutil
from tkinter import filedialog, messagebox
from services.console_service import add_console, get_console_by_id, update_console_settings, get_all_consoles, update_console_orders, delete_console
from services.rom_service import export_roms_to_csv, import_metadata_from_csv

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
# 2. Console Settings Dialog
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
# 3. Reorder Consoles Dialog
# ==========================================
def open_reorder_consoles_dialog(parent, refresh_callback):
    """Popup window to reorder consoles using Up/Down buttons."""
    popup = ctk.CTkToplevel(parent)
    popup.title("Reorder Consoles")
    popup.geometry("350x450")
    popup.grab_set()

    # --- List of Dicts ---
    consoles = get_all_consoles()
    current_order = [{'id': c[0], 'name': c[1]} for c in consoles]

    ctk.CTkLabel(popup, text="Sort Consoles", font=("Arial", 20, "bold")).pack(pady=(15, 5))
    ctk.CTkLabel(popup, text="Use arrows to change the order").pack(pady=(0, 10))

    # --- List Box ---
    list_frame = ctk.CTkScrollableFrame(popup, fg_color="transparent")
    list_frame.pack(fill="both", expand=True, padx=20, pady=5)

    def render_list():
        for w in list_frame.winfo_children():
            w.destroy()
            
        for i, item in enumerate(current_order):
            row = ctk.CTkFrame(list_frame, corner_radius=5)
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"{i+1}. {item['name']}", font=("Arial", 14)).pack(side="left", padx=10, pady=5)

            btn_down = ctk.CTkButton(row, text="▼", width=30, fg_color="#6c757d", command=lambda idx=i: move_down(idx))
            btn_down.pack(side="right", padx=(2, 5), pady=5)
            
            btn_up = ctk.CTkButton(row, text="▲", width=30, fg_color="#6c757d", command=lambda idx=i: move_up(idx))
            btn_up.pack(side="right", padx=2, pady=5)

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
        order_data = [(item['id'], idx) for idx, item in enumerate(current_order)]
        update_console_orders(order_data)
        popup.destroy()
        refresh_callback() 

    ctk.CTkButton(popup, text="💾 Save Order", fg_color="#007bff", command=save_order).pack(pady=15)
    render_list()

# ==========================================
# 4. Confirm Delete Console Dialog
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

# ==========================================
# 5. Export Data
# ==========================================
def open_export_csv_dialog(parent):
    path = filedialog.asksaveasfilename(
        parent=parent, 
        defaultextension=".csv", 
        filetypes=[("CSV Files", "*.csv")], 
        initialfile="retrolist_database.csv"
    )
    if path:
        try:
            export_roms_to_csv(path)
            messagebox.showinfo("Success", "Database exported successfully!\nYou can now open it with Google Sheets or Excel.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

# ==========================================
# 6. Import Data
# ==========================================
def open_import_csv_dialog(parent, refresh_callback):
    path = filedialog.askopenfilename(
        parent=parent,
        filetypes=[("CSV Files", "*.csv")]
    )
    if path:
        try:
            import_metadata_from_csv(path)
            messagebox.showinfo("Success", "Metadata updated from CSV successfully!")
            refresh_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}\n\nPlease make sure you didn't change the column headers.")

# ==========================================
# 7. About Menu
# ==========================================
def open_about_dialog(parent):
    """Popup window showing software information."""
    popup = ctk.CTkToplevel(parent)
    popup.title("About")
    popup.geometry("400x220")
    popup.grab_set()

    ctk.CTkLabel(popup, text="RetroList v0.01", font=("Arial", 28, "bold")).pack(pady=(30, 5))
    ctk.CTkLabel(popup, text="Offline Emulators and Roms Management Software", font=("Arial", 14, "bold")).pack()
    ctk.CTkLabel(popup, text="by Anonymous Serovine 2026", font=("Arial", 12)).pack(pady=(5, 10))
    
    ctk.CTkButton(popup, text="Close", width=100, command=popup.destroy).pack(pady=10)