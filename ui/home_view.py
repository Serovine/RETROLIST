import customtkinter as ctk
import os
from PIL import Image, ImageOps # เพิ่ม ImageOps เพื่อใช้ครอบรูปให้เต็มกรอบ
from tkinter import filedialog, messagebox
from services.console_service import get_all_consoles
from services.rom_service import export_roms_to_csv, import_metadata_from_csv
from ui.dialogs import (
    open_add_console_dialog, 
    open_console_settings_dialog, 
    open_about_dialog,
    open_reorder_consoles_dialog
)

class HomeView(ctk.CTkFrame):
    def __init__(self, master, app_router):
        super().__init__(master, fg_color="transparent")
        self.app_router = app_router
        self.is_fullscreen = False 
        self.cards = [] # เก็บลิสต์ของ Card ทั้งหมดเพื่อใช้จัดเรียงใหม่
        self.current_cols = 4 # ค่าเริ่มต้น

        self.pack(fill="both", expand=True)
        self.render_ui()
        
        # ดักจับ Event เมื่อมีการย่อ/ขยายหน้าต่าง เพื่อคำนวณ Grid ใหม่ (Responsive)
        self.bind("<Configure>", self.on_resize)

    def refresh(self):
        """Clear the frame and re-render the UI."""
        for widget in self.winfo_children():
            widget.destroy()
        self.render_ui()

    def handle_menu(self, choice):
        if choice == "Add Console":
            open_add_console_dialog(self, self.refresh)
        elif choice == "Reorder Consoles":
            open_reorder_consoles_dialog(self, self.refresh)
        elif choice == "Export Data (CSV)": # <--- เพิ่มตรงนี้
            path = filedialog.asksaveasfilename(
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
                    
        elif choice == "Import Data (CSV)": # <--- เพิ่มตรงนี้
            path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
            if path:
                try:
                    import_metadata_from_csv(path)
                    messagebox.showinfo("Success", "Metadata updated from CSV successfully!")
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to import: {e}\n\nPlease make sure you didn't change the column headers.")

        elif choice == "Toggle Fullscreen":
            main_window = self.winfo_toplevel()
            self.is_fullscreen = not self.is_fullscreen
            main_window.attributes("-fullscreen", self.is_fullscreen)
        elif choice == "Options":
            print("Options clicked")
        elif choice == "About":
            open_about_dialog(self)
        
        self.menu_var.set("Menu")

    def on_resize(self, event):
        usable_width = event.width - 25 
        # แก้ตัวหารเป็น 230 เพื่อให้สอดคล้องกับขนาดความกว้างของการ์ดใหม่
        new_cols = max(1, usable_width // 230) 
        
        if new_cols != self.current_cols:
            self.current_cols = new_cols
            self.reorganize_grid()

    def reorganize_grid(self):
        """จัดเรียง Card ใหม่ตามจำนวนคอลัมน์ที่คำนวณได้"""
        for index, card in enumerate(self.cards):
            row = index // self.current_cols
            col = index % self.current_cols
            # วางตำแหน่งใหม่ (ออโต้ปัดบรรทัด)
            card.grid(row=row, column=col, padx=15, pady=15)

    def render_ui(self):
        # ล้างข้อมูลลิสต์การ์ดเก่าทุกครั้งที่มีการ render ใหม่
        self.cards = []

        # --- Top Header ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=20)
        
        lbl_title = ctk.CTkLabel(top_frame, text="EMULATOR & ROM MANAGER", font=("Arial", 28, "bold"))
        lbl_title.pack(side="left", expand=True)
        
        self.menu_var = ctk.StringVar(value="Menu")
        btn_menu = ctk.CTkOptionMenu(
            top_frame, 
            variable=self.menu_var, 
            # เพิ่ม Export / Import เข้าไปในลิสต์
            values=["Add Console", "Reorder Consoles", "Export Data (CSV)", "Import Data (CSV)", "Toggle Fullscreen", "Options", "About"], 
            width=120,
            command=self.handle_menu
        )
        btn_menu.pack(side="right")

        # --- Grid Area ---
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        consoles = get_all_consoles()
        
        if consoles:
            for index, console in enumerate(consoles):
                cid, name, icon_path, count = console
                
                # สร้างกรอบการ์ดหลัก
                card = ctk.CTkFrame(scroll_frame, width=200, height=210, corner_radius=0, fg_color="white", border_width=2, border_color="#343a40")
                card.grid_propagate(False)
                self.cards.append(card) # เก็บเข้าลิสต์ไว้เพื่อใช้ทำ Responsive
                
                # --- Top Area (พื้นที่สีขาว 200x180) ---
                top_area = ctk.CTkFrame(card, width=200, height=180, fg_color="white", corner_radius=0)
                top_area.pack(fill="both", expand=False)
                top_area.pack_propagate(False) # ล็อกขนาดห้ามหด แม้ไม่มีรูป
                
                if icon_path and os.path.exists(icon_path):
                    try:
                        pil_img = Image.open(icon_path)
                        if pil_img.mode in ("RGBA", "P"):
                            pil_img = pil_img.convert("RGB")
                        
                        # ใช้ ImageOps.fit เพื่อครอบรูปให้เต็ม 200x180 เป๊ะๆ โดยไม่เสียสัดส่วน
                        pil_img = pil_img.resize((200, 180), Image.Resampling.LANCZOS)
                        
                        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 180))
                        lbl_icon = ctk.CTkLabel(top_area, text="", image=ctk_img)
                    except:
                        lbl_icon = ctk.CTkLabel(top_area, text="ERR", font=("Arial", 22, "bold"), text_color="red")
                else:
                    # ถ้าไม่มีรูป ให้โชว์ชื่อแทน
                    lbl_icon = ctk.CTkLabel(top_area, text=name.replace(" ", "\n"), font=("Arial", 22, "bold"), text_color="black")
                
                lbl_icon.pack(expand=True, fill="both")
                lbl_icon.bind("<Button-1>", lambda e, c=cid, n=name: self.app_router.show_library(c, n))
                top_area.bind("<Button-1>", lambda e, c=cid, n=name: self.app_router.show_library(c, n))
                
                # --- Bottom Area (แถบดำด้านล่าง 170x30) ---
                bottom_area = ctk.CTkFrame(card, height=30, fg_color="black", corner_radius=0)
                bottom_area.pack(fill="x", side="bottom")
                bottom_area.pack_propagate(False)
                
                # จำนวน Rom
                ctk.CTkLabel(bottom_area, text="Roms", font=("Arial", 12, "bold"), text_color="white").pack(side="left", padx=10)
                ctk.CTkLabel(bottom_area, text=str(count), font=("Arial", 12, "bold"), text_color="#28a745").pack(side="left", expand=True)
                
                # เมนู Setting แต่ละเครื่อง
                lbl_set = ctk.CTkLabel(bottom_area, text="⚙️", font=("Arial", 16), text_color="white", cursor="hand2")
                lbl_set.pack(side="right", padx=10)
                lbl_set.bind("<Button-1>", lambda e, c=cid, n=name: open_console_settings_dialog(self, c, n, self.refresh))
                
        # เรียกจัดเรียง Grid ครั้งแรกตอนโหลดหน้าจอ
        self.reorganize_grid()