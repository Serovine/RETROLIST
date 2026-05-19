import customtkinter as ctk
import ctypes
import os
import sys
from database import init_db
from ui.home_view import HomeView

try:
    myappid = 'serovine.retrolist.app.1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RetroLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RETROLIST")
        self.geometry("800x600")
        self.minsize(980, 720)
        self.iconbitmap(resource_path("app_icon.ico"))
        
        init_db()

        self.current_view = None
        self.show_home()

    def clear_view(self):
        """Destroy the current frame before loading a new one."""
        if self.current_view is not None:
            self.current_view.destroy()

    def show_home(self):
        """Route to Home View."""
        self.clear_view()
        self.current_view = HomeView(master=self, app_router=self)

    def show_library(self, console_id, console_name):
        """Route to Library View."""
        self.clear_view()
        from ui.library_view import LibraryView
        self.current_view = LibraryView(master=self, app_router=self, console_id=console_id, console_name=console_name)

if __name__ == "__main__":
    app = RetroLauncher()
    app.mainloop()