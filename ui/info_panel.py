import customtkinter as ctk
import os
from PIL import Image, ImageOps
from ui.rom_dialogs import open_confirm_delete_dialog, open_edit_rom_dialog
from services.rom_service import launch_game

class InfoPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, refresh_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.refresh_callback = refresh_callback
        
        # --- Placeholder Box 360x270 ---
        self.empty_cover = ctk.CTkImage(light_image=Image.new("RGB", (360, 270), "#2b2b2b"), size=(360, 270))
        self.current_cover_image = None
        
        self.setup_ui()
        self.clear_panel()

    def setup_ui(self):
        top_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        top_wrapper.pack(fill="both", expand=True, pady=20, padx=20) 

        # ==========================================
        # 1. Cover Image
        # ==========================================
        self.lbl_cover = ctk.CTkLabel(top_wrapper, text="", width=360, height=270, fg_color="#2b2b2b", corner_radius=10)
        self.lbl_cover.pack(pady=(0, 20))

        # ==========================================
        # 2. EDIT / Launch
        # ==========================================
        action_frame = ctk.CTkFrame(top_wrapper, fg_color="transparent")
        action_frame.pack(pady=(0, 20))

        self.btn_edit = ctk.CTkButton(action_frame, text="📝 Edit", width=120, fg_color="#6c757d", state="disabled")
        self.btn_edit.pack(side="left", padx=10)

        self.btn_launch = ctk.CTkButton(action_frame, text="▶ Launch", width=120, fg_color="#28a745", state="disabled")
        self.btn_launch.pack(side="left", padx=10)

        # ==========================================
        # 3. METADATA
        # ==========================================
        info_frame = ctk.CTkFrame(top_wrapper, fg_color="transparent")
        info_frame.pack(fill="x", pady=10, padx=10)
        
        # --- Wrap size 350px ---
        self.lbl_title = ctk.CTkLabel(info_frame, text="", font=("Arial", 24, "bold"), justify="left", wraplength=350)
        self.lbl_title.pack(anchor="w", pady=(0, 5))
        
        self.badge_frame = ctk.CTkFrame(info_frame, fg_color="transparent", height=25)
        self.badge_frame.pack(anchor="w", pady=(0, 10))

        font_meta = ("Arial", 14)
        self.lbl_dev = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left")
        self.lbl_dev.pack(anchor="w", pady=3)
        self.lbl_year = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left")
        self.lbl_year.pack(anchor="w", pady=3)
        self.lbl_genre = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left")
        self.lbl_genre.pack(anchor="w", pady=3)
        self.lbl_lang = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left")
        self.lbl_lang.pack(anchor="w", pady=3)
        
        self.lbl_file = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left", wraplength=350)
        self.lbl_file.pack(anchor="w", pady=(15, 0))

        # ==========================================
        # 4. DELETE
        # ==========================================
        bottom_right_frame = ctk.CTkFrame(top_wrapper, fg_color="transparent")
        bottom_right_frame.pack(fill="x", pady=(40, 10)) 
        
        self.btn_delete = ctk.CTkButton(bottom_right_frame, text="🗑️ Delete ROM", width=120, fg_color="#dc3545", state="disabled")
        self.btn_delete.pack(side="right")

    def clear_panel(self):
        self.lbl_cover.configure(image=self.empty_cover, text="NO COVER", text_color="gray", fg_color="#2b2b2b")
        self.lbl_title.configure(text="")
        self.lbl_dev.configure(text="")
        self.lbl_year.configure(text="")
        self.lbl_genre.configure(text="")
        self.lbl_lang.configure(text="")
        self.lbl_file.configure(text="")
        for w in self.badge_frame.winfo_children(): w.destroy()
        self.btn_launch.configure(state="disabled", fg_color="gray")
        self.btn_edit.configure(state="disabled")
        self.btn_delete.configure(state="disabled")

    def update_info(self, rom, master_window):
        rom_id = rom.get('id', rom.get('rom_id', 0))
        is_exists = rom.get('is_exists', True)

        cover_path = rom.get('cover_path')
        if cover_path and os.path.exists(cover_path):
            try:
                pil_img = Image.open(cover_path)
                if pil_img.mode in ("RGBA", "P"): pil_img = pil_img.convert("RGB")
                pil_img = ImageOps.contain(pil_img, (360, 270), Image.Resampling.LANCZOS)
                self.current_cover_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                self.lbl_cover.configure(image=self.current_cover_image, text="", fg_color="transparent")
            except:
                self.current_cover_image = None
                self.lbl_cover.configure(image=self.empty_cover, text="IMAGE ERROR", text_color="#dc3545", fg_color="#2b2b2b")
        else:
            self.current_cover_image = None
            self.lbl_cover.configure(image=self.empty_cover, text="NO COVER", text_color="gray", fg_color="#2b2b2b")

        title_color = "white" if is_exists else "#ff4c4c"
        self.lbl_title.configure(text=rom.get('game_name', 'Unknown'), text_color=title_color)

        self.lbl_genre.configure(text=f"🎮 : {rom.get('genre', '')}")        
        self.lbl_year.configure(text=f"📅 : {rom.get('release_year', '')}")
        self.lbl_dev.configure(text=f"🏢 : {rom.get('developer', '')}")
        self.lbl_lang.configure(text=f"🌐 : {rom.get('language', 'Unknown')}")
        
        status_text = "" if is_exists else " [FILE MISSING]"
        self.lbl_file.configure(text=f"File : {rom.get('file_name', '')}{status_text}", text_color="#adb5bd" if is_exists else "#ff4c4c")

        for w in self.badge_frame.winfo_children(): w.destroy()
            
        if rom.get('is_hack') == 1:
            ctk.CTkLabel(self.badge_frame, text=" HACK ", font=("Arial", 11, "bold"), fg_color="#ffc107", text_color="black", corner_radius=4).pack(side="left", padx=3)
        if rom.get('is_translated') == 1:
            ctk.CTkLabel(self.badge_frame, text=" TRANSLATED ", font=("Arial", 11, "bold"), fg_color="#17a2b8", text_color="white", corner_radius=4).pack(side="left", padx=3)

        self.btn_launch.configure(
            state="normal" if is_exists else "disabled",
            fg_color="#28a745" if is_exists else "gray",
            text="▶ Launch" if is_exists else "Missing",
            command=lambda e=rom.get('emu_path'), r=rom.get('full_rom_path'): launch_game(e, r)
        )
        
        self.btn_edit.configure(
            state="normal",
            command=lambda r=rom: open_edit_rom_dialog(master_window, r, self.refresh_callback)
        )
        
        self.btn_delete.configure(
            state="normal",
            command=lambda rid=rom_id, gname=rom.get('game_name', 'Unknown'): open_confirm_delete_dialog(master_window, rid, gname, self.refresh_callback)
        )