import customtkinter as ctk
import math
import os
import textwrap
from PIL import Image, ImageOps
from services.rom_service import get_roms_for_console, get_rom_count

class RomListPanel(ctk.CTkFrame):
    def __init__(self, master, console_id, on_game_selected_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.console_id = console_id
        self.on_game_selected_callback = on_game_selected_callback
        
        self.current_sort = "Added (Newest)" 
        self.current_search = ""
        self.current_genre = "All"
        self.current_page = 1
        self.items_per_page = "20"
        self.current_view_mode = "List" # โหมดเริ่มต้น
        
        self.list_buttons = []
        self.selected_rom_id = None

        # รูปใสสำหรับตอนที่เกมไม่มีหน้าปก (ขนาด Thumbnail 100x100)
        self.empty_thumb = ctk.CTkImage(light_image=Image.new("RGBA", (100, 100), (0, 0, 0, 0)), size=(100, 100))
        
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Game List", font=("Arial", 16, "bold"), anchor="w", fg_color="#1f1f1f", corner_radius=5).pack(fill="x", padx=10, pady=10, ipady=5)
        self.list_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.page_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.page_frame.pack(fill="x", side="bottom", pady=5)

    def apply_filters(self, search, genre, sort, limit, view_mode="List"):
        self.current_search = search
        self.current_genre = genre
        self.current_sort = sort
        self.items_per_page = limit
        self.current_view_mode = view_mode
        self.current_page = 1
        self.fetch_data()

    def change_page(self, direction):
        self.current_page += direction
        self.fetch_data()

    def fetch_data(self):
        for widget in self.list_scroll.winfo_children(): widget.destroy()
        for widget in self.page_frame.winfo_children(): widget.destroy()

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
            ctk.CTkLabel(self.list_scroll, text="No ROMs found.", text_color="gray").pack(pady=20)
            self.on_game_selected_callback(None)
        else:
            target_index = 0
            target_rom = roms[0]
            
            for index, rom in enumerate(roms):
                game_name = rom.get('game_name', 'Unknown')
                is_exists = rom.get('is_exists', True)
                text_color = "white" if is_exists else "#ff4c4c"

                if self.current_view_mode == "List":
                    # ====================================
                    # โหมด List (แบบเดิม)
                    # ====================================
                    btn_game = ctk.CTkButton(
                        self.list_scroll, 
                        text=f"{offset_val + index + 1}.  {game_name}", 
                        anchor="w", fg_color="transparent", 
                        text_color=text_color, font=("Arial", 14),
                        hover_color="#2a4b6e",  
                        cursor="hand2"
                    )
                    btn_game.pack(fill="x", pady=2, ipady=2)
                
                else:
                    # ====================================
                    # โหมด Grid (แบบใหม่: มีรูปโชว์รูป / ไม่มีรูปโชว์กล่องข้อความ)
                    # ====================================
                    cover_path = rom.get('cover_path')
                    has_cover = False
                    
                    # 1. เช็กก่อนว่ามีไฟล์รูปจริงๆ ไหม
                    if cover_path and os.path.exists(cover_path):
                        try:
                            pil_img = Image.open(cover_path).convert("RGB")
                            pil_img = ImageOps.contain(pil_img, (100, 100), Image.Resampling.LANCZOS)
                            thumb_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100, 100))
                            has_cover = True
                        except:
                            pass

                    # 2. สร้างปุ่มตามสถานะของรูป
                    if has_cover:
                        # กรณีมีรูป: โชว์รูป แล้วใส่ชื่อสั้นๆ ไว้ใต้รูปเหมือนเดิม
                        short_name = game_name[:12] + "..." if len(game_name) > 12 else game_name
                        btn_game = ctk.CTkButton(
                            self.list_scroll, 
                            image=thumb_img,
                            text="",
                            compound="top",
                            fg_color="transparent", 
                            text_color=text_color, font=("Arial", 12),
                            width=120, height=140,
                            hover_color="#2a4b6e",  
                            cursor="hand2"
                        )
                    else:
                        # กรณีไม่มีรูป: ทำปุ่มเป็นกล่องสีเทา แล้วหั่นชื่อเกมเป็นบรรทัดๆ ให้อยู่ตรงกลาง
                        # หั่นข้อความบรรทัดละประมาณ 12 ตัวอักษร
                        wrapped_name = "\n".join(textwrap.wrap(game_name, width=12))
                        
                        # ป้องกันข้อความยาวเกินไปจนล้นกล่อง (จำกัดแค่ 4 บรรทัด)
                        lines = wrapped_name.split('\n')
                        if len(lines) > 4: 
                            wrapped_name = "\n".join(lines[:3]) + "\n..."

                        btn_game = ctk.CTkButton(
                            self.list_scroll, 
                            text=wrapped_name,
                            fg_color="#2b2b2b", # ทำพื้นหลังเป็นกล่องสีเทา
                            text_color=text_color, font=("Arial", 13, "bold"),
                            width=120, height=140,corner_radius=8,
                            hover_color="#2a4b6e",  
                            cursor="hand2"
                        )
                    
                    # 3. จัดเรียงลง Grid (3 คอลัมน์)
                    columns = 3
                    row_idx = index // columns
                    col_idx = index % columns
                    btn_game.grid(row=row_idx, column=col_idx, padx=5, pady=5)

                # ผูกคำสั่งเมื่อคลิกเหมือนเดิม
                btn_game.configure(command=lambda r=rom, b=btn_game: self.select_game(r, b))
                self.list_buttons.append(btn_game)

                # จำเกมที่เคยเลือก
                if hasattr(self, 'selected_rom_id') and rom.get('id', rom.get('rom_id', 0)) == self.selected_rom_id:
                    target_index = index
                    target_rom = rom

            if self.list_buttons:
                self.select_game(target_rom, self.list_buttons[target_index])

        # Pagination
        if limit_val != "All" and total_pages > 1:
            btn_prev = ctk.CTkButton(self.page_frame, text="<", width=30, command=lambda: self.change_page(-1))
            btn_prev.pack(side="left", padx=10)
            if self.current_page <= 1: btn_prev.configure(state="disabled", fg_color="gray")

            ctk.CTkLabel(self.page_frame, text=f"{self.current_page} / {total_pages}", font=("Arial", 12)).pack(side="left", expand=True)

            btn_next = ctk.CTkButton(self.page_frame, text=">", width=30, command=lambda: self.change_page(1))
            btn_next.pack(side="right", padx=10)
            if self.current_page >= total_pages: btn_next.configure(state="disabled", fg_color="gray")

    def select_game(self, rom, selected_btn):
        self.selected_rom_id = rom.get('id', rom.get('rom_id', 0))
        for btn in self.list_buttons:
            btn.configure(fg_color="transparent")
        selected_btn.configure(fg_color="#007bff") 
        self.on_game_selected_callback(rom)