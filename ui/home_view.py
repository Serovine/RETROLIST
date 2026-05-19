import customtkinter as ctk
import os
from PIL import Image, ImageOps

from services.console_service import get_all_consoles
from ui.console_dialogs import (
    open_add_console_dialog, 
    open_console_settings_dialog, 
    open_reorder_consoles_dialog, 
    open_about_dialog,
    open_export_csv_dialog,
    open_import_csv_dialog
)

class HomeView(ctk.CTkFrame):
    def __init__(self, master, app_router):
        super().__init__(master, fg_color="transparent")
        self.app_router = app_router
        self.is_fullscreen = False 
        self.cards = []
        self.current_cols = 4

        self.pack(fill="both", expand=True)
        self.render_ui()
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
        elif choice == "Export Data (CSV)":
            open_export_csv_dialog(self)
        elif choice == "Import Data (CSV)":
            open_import_csv_dialog(self, self.refresh)
        elif choice == "Toggle Fullscreen":
            main_window = self.winfo_toplevel()
            self.is_fullscreen = not self.is_fullscreen
            main_window.attributes("-fullscreen", self.is_fullscreen)
        elif choice == "Options":
            print("Options clicked")
        elif choice == "About":
            open_about_dialog(self)
        
        self.menu_var.set("☰")

    def on_resize(self, event):
        usable_width = event.width - 25 
        new_cols = max(1, usable_width // 230) 
        
        if new_cols != self.current_cols:
            self.current_cols = new_cols
            self.reorganize_grid()

    def reorganize_grid(self):
        for index, card in enumerate(self.cards):
            row = index // self.current_cols
            col = index % self.current_cols
            card.grid(row=row, column=col, padx=15, pady=15)

    def render_ui(self):
        self.cards = []

        # --- Top Header ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=20)
        
        lbl_title = ctk.CTkLabel(top_frame, text="EMULATOR & ROM MANAGER", font=("Arial", 28, "bold"))
        lbl_title.pack(side="left", expand=True)
        
        self.menu_var = ctk.StringVar(value="☰")
        btn_menu = ctk.CTkOptionMenu(
            top_frame, 
            variable=self.menu_var, 
            values=["Add Console", "Reorder Consoles", "Export Data (CSV)", "Import Data (CSV)", "Toggle Fullscreen", "About"], 
            width=60,
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
                
                # Create Main Grid
                card = ctk.CTkFrame(scroll_frame, width=200, height=210, corner_radius=0, fg_color="black", border_width=2, border_color="#343a40")
                card.grid_propagate(False)
                self.cards.append(card) # เก็บเข้าลิสต์ไว้เพื่อใช้ทำ Responsive
                
                # --- Top Area (200x180) ---
                top_area = ctk.CTkFrame(card, width=200, height=180, fg_color="black", corner_radius=0)
                top_area.pack(fill="both", expand=False)
                top_area.pack_propagate(False)
                
                if icon_path and os.path.exists(icon_path):
                    try:
                        pil_img = Image.open(icon_path)
                        if pil_img.mode in ("RGBA", "P"):
                            pil_img = pil_img.convert("RGB")
                        
                        pil_img = pil_img.resize((200, 180), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 180))
                        
                        btn_icon = ctk.CTkButton(
                            top_area, text="", image=ctk_img, 
                            fg_color="transparent", hover_color="#e2e6ea",
                            corner_radius=0, cursor="hand2",
                            command=lambda c=cid, n=name: self.app_router.show_library(c, n)
                        )
                    except:
                        btn_icon = ctk.CTkButton(
                            top_area, text="ERR", font=("Arial", 22, "bold"), text_color="red", 
                            fg_color="transparent", hover_color="#e2e6ea", 
                            corner_radius=0, cursor="hand2",
                            command=lambda c=cid, n=name: self.app_router.show_library(c, n)
                        )
                else:
                    # --- No image ---
                    btn_icon = ctk.CTkButton(
                        top_area, text=name.replace(" ", "\n"), font=("Arial", 22, "bold"), text_color="green", 
                        fg_color="transparent", hover_color="#e2e6ea", 
                        corner_radius=0, cursor="hand2",
                        command=lambda c=cid, n=name: self.app_router.show_library(c, n)
                    )
                
                btn_icon.pack(expand=True, fill="both")

                # --- Bottom Area (170x30) ---
                bottom_area = ctk.CTkFrame(card, height=30, fg_color="black", corner_radius=0)
                bottom_area.pack(fill="x", side="bottom")
                bottom_area.pack_propagate(False)
                
                # --- Rom Number ---
                ctk.CTkLabel(bottom_area, text="Roms", font=("Arial", 12, "bold"), text_color="white").pack(side="left", padx=10)
                ctk.CTkLabel(bottom_area, text=str(count), font=("Arial", 12, "bold"), text_color="#28a745").pack(side="left", expand=True)
                
                # ---Console Setting ---
                lbl_set = ctk.CTkLabel(bottom_area, text="⚙️", font=("Arial", 16), text_color="white", cursor="hand2")
                lbl_set.pack(side="right", padx=10)
                lbl_set.bind("<Button-1>", lambda e, c=cid, n=name: open_console_settings_dialog(self, c, n, self.refresh))
                
        self.reorganize_grid()