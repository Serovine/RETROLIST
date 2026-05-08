import customtkinter as ctk
from database import init_db
from ui.home_view import HomeView
# from ui.library_view import LibraryView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RetroLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RETROLIST")
        self.geometry("800x600")
        
        init_db()

        self.current_view = None # เก็บสถานะว่าตอนนี้เปิดหน้าไหนอยู่
        self.show_home()

    def clear_view(self):
        """Destroy the current frame before loading a new one."""
        if self.current_view is not None:
            self.current_view.destroy()

    def show_home(self):
        """Route to Home View."""
        self.clear_view()
        # ส่ง self (ตัว Router) เข้าไปให้ HomeView ใช้เรียกเปลี่ยนหน้า
        self.current_view = HomeView(master=self, app_router=self)

    def show_library(self, console_id, console_name):
        """Route to Library View."""
        self.clear_view()
        # นำเข้า LibraryView จากโฟลเดอร์ ui
        from ui.library_view import LibraryView
        self.current_view = LibraryView(master=self, app_router=self, console_id=console_id, console_name=console_name)

if __name__ == "__main__":
    app = RetroLauncher()
    app.mainloop()