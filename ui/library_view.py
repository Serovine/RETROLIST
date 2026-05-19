import customtkinter as ctk
import threading
from ui.info_panel import InfoPanel
from ui.romlist_panel import RomListPanel
from services.rom_service import get_genres_for_console, scan_and_add_roms

class LibraryView(ctk.CTkFrame):
    def __init__(self, master, app_router, console_id, console_name):
        super().__init__(master, fg_color="transparent")
        self.app_router = app_router
        self.console_id = console_id
        self.console_name = console_name
        
        self.pack(fill="both", expand=True)
        self.render_ui()

    def go_back(self):
        self.destroy()
        self.app_router.show_home()

    # --- 1. Prevent Repeating Click ---
    def handle_scan(self):
        self.btn_scan.configure(text="⏳ Scanning...", state="disabled", fg_color="#6c757d")
        
    # --- 2. Thread Work Solution ---
        def scan_task():
            scan_and_add_roms(self.console_id)
            self.after(0, self.on_scan_complete)
            
        threading.Thread(target=scan_task, daemon=True).start()

    # --- 3. Refresh List ---
    def on_scan_complete(self):
        self.btn_scan.configure(text="🔄 Scan ROMs", state="normal", fg_color="#007bff")
        self.list_panel.fetch_data()
        
    def refresh_from_edit(self):
        self.list_panel.fetch_data()

    def trigger_filters(self, *args):
        search = self.search_entry.get().strip()
        genre = self.genre_var.get()
        sort = self.sort_var.get()
        limit = self.limit_var.get()
        view_mode = self.view_mode_var.get() 
        self.list_panel.apply_filters(search, genre, sort, limit, view_mode)

    def on_game_selected(self, rom_data):
        if rom_data:
            self.info_panel.update_info(rom_data, self)
        else:
            self.info_panel.clear_panel()

    def render_ui(self):
        # --- Top Header ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        btn_back = ctk.CTkButton(top_frame, text="< Back", width=80, command=self.go_back)
        btn_back.pack(side="left")
        
        lbl_title = ctk.CTkLabel(top_frame, text=f"{self.console_name} Library", font=("Arial", 24, "bold"))
        lbl_title.pack(side="left", padx=20)

        # --- Toggle List/Grid ---
        self.view_mode_var = ctk.StringVar(value="List")
        view_toggle = ctk.CTkSegmentedButton(top_frame, values=["List", "Grid"], variable=self.view_mode_var, command=self.trigger_filters)
        view_toggle.pack(side="right", padx=(0, 20))

        self.btn_scan = ctk.CTkButton(top_frame, text="🔄 Scan ROMs", width=100, fg_color="#007bff", hover_color="#0056b3", command=self.handle_scan)
        self.btn_scan.pack(side="right", padx=20)

        # --- Filter Toolbar ---
        tool_frame = ctk.CTkFrame(self, fg_color="transparent")
        tool_frame.pack(fill="x", padx=20, pady=(10, 10))

        self.search_entry = ctk.CTkEntry(tool_frame, placeholder_text="Search game...", width=180)
        self.search_entry.pack(side="left", padx=(0, 5))
        ctk.CTkButton(tool_frame, text="🔍", width=40, command=self.trigger_filters).pack(side="left", padx=(0, 20))

        available_genres = get_genres_for_console(self.console_id)
        ctk.CTkLabel(tool_frame, text="Genre:").pack(side="left")
        self.genre_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(tool_frame, variable=self.genre_var, values=available_genres, command=self.trigger_filters, width=120).pack(side="left", padx=(5, 20))

        ctk.CTkLabel(tool_frame, text="Sort by:").pack(side="left")
        self.sort_var = ctk.StringVar(value="Added (Newest)")
        ctk.CTkOptionMenu(tool_frame, variable=self.sort_var, values=["Added (Newest)", "Added (Oldest)", "Name (A-Z)", "Name (Z-A)", "Year (New-Old)", "Year (Old-New)", "Genre"], command=self.trigger_filters, width=140).pack(side="left", padx=(5, 20))

        ctk.CTkLabel(tool_frame, text="Show:").pack(side="left")
        self.limit_var = ctk.StringVar(value="20")
        ctk.CTkOptionMenu(tool_frame, variable=self.limit_var, values=["20", "50", "100", "All"], command=self.trigger_filters, width=80).pack(side="left", padx=(5, 0))

        # --- Main Split Layout ---
        main_split_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_split_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # Rom List Column Lock at 420px
        main_split_frame.grid_columnconfigure(0, weight=0, minsize=420)
        main_split_frame.grid_columnconfigure(1, weight=1)
        main_split_frame.grid_rowconfigure(0, weight=1)

        self.list_panel = RomListPanel(main_split_frame, console_id=self.console_id, on_game_selected_callback=self.on_game_selected, fg_color="#2b2b2b", corner_radius=10)
        self.list_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        self.info_panel = InfoPanel(main_split_frame, refresh_callback=self.refresh_from_edit, fg_color="#212121", corner_radius=10)
        self.info_panel.grid(row=0, column=1, sticky="nsew")

        self.list_panel.fetch_data()