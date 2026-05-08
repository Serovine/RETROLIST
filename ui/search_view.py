import customtkinter as ctk
from database import search_games


class SearchView(ctk.CTkFrame):
    def __init__(self, master, callbacks):
        super().__init__(master)

        self.on_back = callbacks["back"]
        self.on_launch = callbacks["launch"]

        self.pack(fill="both", expand=True)

        self.render()

    def render(self):
        # TOP
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(top, text="< Back", command=self.on_back).pack(side="left")

        self.entry = ctk.CTkEntry(top, placeholder_text="Search game...")
        self.entry.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(top, text="Search", command=self.do_search).pack(side="left")

        # RESULT AREA
        self.result_frame = ctk.CTkScrollableFrame(self)
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def do_search(self):
        keyword = self.entry.get().strip()

        for w in self.result_frame.winfo_children():
            w.destroy()

        if not keyword:
            return

        results = search_games(keyword)

        if not results:
            ctk.CTkLabel(self.result_frame, text="No results").pack(pady=20)
            return

        for rom_id, name, file, console_name, console_id in results:
            row = ctk.CTkFrame(self.result_frame)
            row.pack(fill="x", pady=5)

            ctk.CTkLabel(
                row,
                text=f"{name}  [{console_name}]",
                font=("Arial", 14)
            ).pack(side="left", padx=10)

            ctk.CTkButton(
                row,
                text="Launch",
                command=lambda rid=rom_id, cid=console_id: self.on_launch(rid, cid)
            ).pack(side="right", padx=10)