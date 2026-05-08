import customtkinter as ctk
import os
import math
from PIL import Image, ImageOps
from ui.dialogs import open_confirm_delete_dialog, open_edit_rom_dialog
from services.rom_service import get_roms_for_console, launch_game, get_genres_for_console, get_rom_count, scan_and_add_roms

class LibraryView(ctk.CTkFrame):
    def __init__(self, master, app_router, console_id, console_name):
        super().__init__(master, fg_color="transparent")
        self.app_router = app_router
        self.console_id = console_id
        self.console_name = console_name
        
        self.current_sort = "Added (Newest)" 
        self.current_search = ""
        self.current_genre = "All"
        self.current_page = 1
        self.items_per_page = "20"
        
        self.list_buttons = [] 
        self.current_cover_image = None 
        self.empty_cover = ctk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))

        self.pack(fill="both", expand=True)
        self.render_ui()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.render_ui()

    def go_back(self):
        self.destroy()
        self.app_router.show_home()

    def do_search(self, search_term):
        self.current_search = search_term
        self.current_page = 1
        self.refresh()

    def do_genre_filter(self, choice):
        self.current_genre = choice
        self.current_page = 1
        self.refresh()

    def handle_sort_change(self, choice):
        self.current_sort = choice
        self.current_page = 1
        self.refresh()

    def handle_limit_change(self, choice):
        self.items_per_page = choice
        self.current_page = 1
        self.refresh()

    def change_page(self, direction):
        self.current_page += direction
        self.refresh()

    def handle_scan(self):
        scan_and_add_roms(self.console_id)
        self.current_page = 1
        self.refresh()
        
    def handle_save_metadata(self, updated_data=None):
        self.refresh()
        
    def handle_delete(self):
        self.refresh()

    def render_ui(self):
        # --- Top Header ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        btn_back = ctk.CTkButton(top_frame, text="< Back", width=80, command=self.go_back)
        btn_back.pack(side="left")
        
        lbl_title = ctk.CTkLabel(top_frame, text=f"{self.console_name} Library", font=("Arial", 24, "bold"))
        lbl_title.pack(side="left", padx=20)

        btn_scan = ctk.CTkButton(top_frame, text="🔄 Scan ROMs", width=100, fg_color="#007bff", hover_color="#0056b3", command=self.handle_scan)
        btn_scan.pack(side="right", padx=20)

        # --- Filter Toolbar ---
        tool_frame = ctk.CTkFrame(self, fg_color="transparent")
        tool_frame.pack(fill="x", padx=20, pady=(10, 10))

        search_entry = ctk.CTkEntry(tool_frame, placeholder_text="Search game...", width=180)
        search_entry.pack(side="left", padx=(0, 5))
        if self.current_search: search_entry.insert(0, self.current_search)
        ctk.CTkButton(tool_frame, text="🔍", width=40, command=lambda: self.do_search(search_entry.get().strip())).pack(side="left", padx=(0, 20))

        available_genres = get_genres_for_console(self.console_id)
        ctk.CTkLabel(tool_frame, text="Genre:").pack(side="left")
        ctk.CTkOptionMenu(tool_frame, variable=ctk.StringVar(value=self.current_genre), values=available_genres, command=self.do_genre_filter, width=120).pack(side="left", padx=(5, 20))

        ctk.CTkLabel(tool_frame, text="Sort by:").pack(side="left")
        ctk.CTkOptionMenu(tool_frame, variable=ctk.StringVar(value=self.current_sort), values=["Added (Newest)", "Added (Oldest)", "Name (A-Z)", "Name (Z-A)", "Year (New-Old)", "Year (Old-New)", "Genre"], command=self.handle_sort_change, width=140).pack(side="left", padx=(5, 20))

        ctk.CTkLabel(tool_frame, text="Show:").pack(side="left")
        ctk.CTkOptionMenu(tool_frame, variable=ctk.StringVar(value=self.items_per_page), values=["20", "50", "100", "All"], command=self.handle_limit_change, width=80).pack(side="left", padx=(5, 0))

        # --- Main Split Layout ---
        main_split_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_split_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # ส่วนซ้าย: Game List
        left_panel = ctk.CTkFrame(main_split_frame, width=350, fg_color="#2b2b2b", corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False) 
        
        ctk.CTkLabel(left_panel, text="Game List", font=("Arial", 16, "bold"), anchor="w", fg_color="#1f1f1f", corner_radius=5).pack(fill="x", padx=10, pady=10, ipady=5)
        
        list_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # ส่วนขวา: Metadata Panel
        right_panel = ctk.CTkScrollableFrame(main_split_frame, fg_color="#212121", corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.setup_details_panel(right_panel)

        # --- Data Fetching & Pagination ---
        total_items = get_rom_count(self.console_id, self.current_search, self.current_genre)
        limit_val = self.items_per_page
        offset_val = 0
        total_pages = 1

        if limit_val != "All":
            limit_int = int(limit_val)
            total_pages = math.ceil(total_items / limit_int) if total_items > 0 else 1
            offset_val = (self.current_page - 1) * limit_int
            if self.current_page > total_pages and total_pages > 0: 
                self.current_page = total_pages
                offset_val = (self.current_page - 1) * limit_int

        roms = get_roms_for_console(self.console_id, self.current_sort, self.current_search, self.current_genre, limit=limit_val, offset=offset_val)

        self.list_buttons = []
        if not roms:
            ctk.CTkLabel(list_scroll, text="No ROMs found.", text_color="gray").pack(pady=20)
            self.clear_details_panel()
        else:
            target_index = 0
            target_rom = roms[0]
            
            for index, rom in enumerate(roms):
                btn_game = ctk.CTkButton(
                    list_scroll, 
                    text=f"{offset_val + index + 1}.  {rom.get('game_name', 'Unknown')}", 
                    anchor="w", 
                    fg_color="transparent", 
                    text_color="white" if rom.get('is_exists', True) else "#ff4c4c",
                    hover_color="#343a40",
                    font=("Arial", 14)
                )
                btn_game.pack(fill="x", pady=2, ipady=2)
                btn_game.configure(command=lambda r=rom, b=btn_game: self.on_game_selected(r, b))
                self.list_buttons.append(btn_game)

                # ดึงสถานะการจำ ID กลับมาใช้
                if hasattr(self, 'selected_rom_id') and rom.get('id', rom.get('rom_id', 0)) == self.selected_rom_id:
                    target_index = index
                    target_rom = rom

            if self.list_buttons:
                self.on_game_selected(target_rom, self.list_buttons[target_index])

        if limit_val != "All" and total_pages > 1:
            page_frame = ctk.CTkFrame(left_panel, fg_color="transparent", height=40)
            page_frame.pack(fill="x", side="bottom", pady=5)
            
            btn_prev = ctk.CTkButton(page_frame, text="<", width=30, command=lambda: self.change_page(-1))
            btn_prev.pack(side="left", padx=10)
            if self.current_page <= 1: btn_prev.configure(state="disabled", fg_color="gray")

            ctk.CTkLabel(page_frame, text=f"{self.current_page} / {total_pages}", font=("Arial", 12)).pack(side="left", expand=True)

            btn_next = ctk.CTkButton(page_frame, text=">", width=30, command=lambda: self.change_page(1))
            btn_next.pack(side="right", padx=10)
            if self.current_page >= total_pages: btn_next.configure(state="disabled", fg_color="gray")

    def setup_details_panel(self, parent_frame):
        # ดันข้อมูลขึ้นข้างบนด้วย anchor="n"
        top_wrapper = ctk.CTkFrame(parent_frame, fg_color="transparent")
        top_wrapper.pack(fill="x", pady=20, padx=40, anchor="n")

        # 1. Cover Image (ขยายขนาดเป็น 400x400)
        self.lbl_cover = ctk.CTkLabel(top_wrapper, text="", width=400, height=400, fg_color="#1a1a1a", corner_radius=10)
        self.lbl_cover.pack(pady=(0, 20))

        # 2. Action Buttons 
        action_frame = ctk.CTkFrame(top_wrapper, fg_color="transparent")
        action_frame.pack(pady=(0, 20))

        self.btn_edit = ctk.CTkButton(action_frame, text="📝 Edit", width=120, fg_color="#6c757d", state="disabled")
        self.btn_edit.pack(side="left", padx=10)

        self.btn_launch = ctk.CTkButton(action_frame, text="▶ Launch", width=120, fg_color="#28a745", state="disabled")
        self.btn_launch.pack(side="left", padx=10)

        # 3. Metadata Info (จัดใหม่ให้เรียงทีละบรรทัด)
        info_frame = ctk.CTkFrame(top_wrapper, fg_color="transparent")
        info_frame.pack(fill="x", pady=10)
        
        # เพิ่ม wraplength เข้าไปเพื่อให้ชื่อเกมขึ้นบรรทัดใหม่แทนการโดนตัดขอบหาย
        self.lbl_title = ctk.CTkLabel(info_frame, text="", font=("Arial", 28, "bold"), justify="left", wraplength=450)
        self.lbl_title.pack(anchor="w", pady=(0, 5))
        
        self.badge_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        self.badge_frame.pack(anchor="w", pady=(0, 15))

        font_meta = ("Arial", 16)
        self.lbl_dev = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left")
        self.lbl_dev.pack(anchor="w", pady=3)
        
        self.lbl_year = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left")
        self.lbl_year.pack(anchor="w", pady=3)

        self.lbl_genre = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left")
        self.lbl_genre.pack(anchor="w", pady=3)

        self.lbl_lang = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left")
        self.lbl_lang.pack(anchor="w", pady=3)
        
        # เพิ่ม wraplength ให้ชื่อไฟล์ด้วยเผื่อชื่อไฟล์ยาวมาก
        self.lbl_file = ctk.CTkLabel(info_frame, text="", font=font_meta, text_color="#adb5bd", justify="left", wraplength=450)
        self.lbl_file.pack(anchor="w", pady=(15, 0))

        # 4. Delete Button
        bottom_right_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        bottom_right_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.btn_delete = ctk.CTkButton(bottom_right_frame, text="🗑️ Delete ROM", width=120, fg_color="#dc3545", state="disabled")
        self.btn_delete.pack(side="right")

    def clear_details_panel(self):
        self.lbl_cover.configure(image=self.empty_cover, text="No Game Selected", fg_color="#1a1a1a")
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

    def on_game_selected(self, rom, selected_btn):
        rom_id = rom.get('id', rom.get('rom_id', 0))
        is_exists = rom.get('is_exists', True)
        self.selected_rom_id = rom_id # จำ ID เผื่ออัปเดตหน้าจอ

        for btn in self.list_buttons:
            btn.configure(fg_color="transparent")
        selected_btn.configure(fg_color="#007bff") 

        cover_path = rom.get('cover_path')
        if cover_path and os.path.exists(cover_path):
            try:
                pil_img = Image.open(cover_path)
                if pil_img.mode in ("RGBA", "P"): pil_img = pil_img.convert("RGB")
                # ขยายเป็น 400x400 รับกับหน้าจอ 
                pil_img = ImageOps.contain(pil_img, (400, 400), Image.Resampling.LANCZOS)
                self.current_cover_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                self.lbl_cover.configure(image=self.current_cover_image, text="", fg_color="transparent")
            except:
                self.current_cover_image = None
                self.lbl_cover.configure(image=self.empty_cover, text="IMAGE ERROR", fg_color="#dc3545")
        else:
            self.current_cover_image = None
            self.lbl_cover.configure(image=self.empty_cover, text="NO COVER", fg_color="#495057")

        title_color = "white" if is_exists else "#ff4c4c"
        self.lbl_title.configure(text=rom.get('game_name', 'Unknown'), text_color=title_color)
        
        # ใส่ข้อมูลลงบรรทัดแยกตามที่คุณต้องการ
        self.lbl_dev.configure(text=f"Developer : {rom.get('developer', '')}")
        self.lbl_year.configure(text=f"Year : {rom.get('release_year', '')}")
        self.lbl_genre.configure(text=f"Genre : {rom.get('genre', '')}")
        self.lbl_lang.configure(text=f"Language : {rom.get('language', 'Unknown')}")
        
        status_text = "" if is_exists else " [FILE MISSING]"
        self.lbl_file.configure(text=f"File : {rom.get('file_name', '')}{status_text}", text_color="#adb5bd" if is_exists else "#ff4c4c")

        for w in self.badge_frame.winfo_children():
            w.destroy()
            
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
            command=lambda r=rom: open_edit_rom_dialog(self, r, self.handle_save_metadata)
        )
        
        self.btn_delete.configure(
            state="normal",
            command=lambda rid=rom_id, gname=rom.get('game_name', 'Unknown'): open_confirm_delete_dialog(self, rid, gname, self.handle_delete)
        )