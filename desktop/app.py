import os
import customtkinter as ctk
from PIL import Image

from components.Loader import Loader
from components.tabs.SelectionTab import SelectionTab
from components.tabs.LinkTab import LinkTab
from components.tabs.UploadTab import UploadTab

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FotoModelApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.CARD_WIDTH  = 268
        self.CARD_HEIGHT = 151
        self.COLS = 5
        self.window_width  = 1600
        self.window_height = 900

        # ---------------- Window ----------------
        self.title("Foto Model Studio")
        
        #self.geometry("1600x1000")
        self.center_window(self.window_width, self.window_height, self)
        self.COLS = self.resize_window(self.COLS, self.CARD_WIDTH, self)

        self.create_ui()

        # -------------- Spinner --------------
        self.spinner = Loader(self)

    def center_window(self, width, height, window):
        window.update_idletasks()
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()

        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)

        window.resizable(False, False)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def set_sizes(self):
        return self.COLS, self.CARD_WIDTH, self.CARD_HEIGHT

    def resize_window(self, cols, card_width, window):
        content_width = cols * card_width + 260
        window_width  = window.winfo_width()

        if content_width > window_width:
            print(content_width, window_width)
            cols = window_width // card_width
            print(cols)

        return cols

    # ---------------- UI ----------------
    def create_ui(self):
        # self.create_header()
        self.create_tabs()
        self.create_log_tab()

    # ---------------- Header ----------------
    """def create_header(self):
        header = ctk.CTkFrame(self, height=100, corner_radius=0)
        header.pack(fill="x")

        if os.path.exists("logo.jpg"):
            logo_img = Image.open("logo.jpg").resize((100, 100))
            self.logo = ctk.CTkImage(logo_img)

            ctk.CTkLabel(
                header,
                image=self.logo,
                text="",
                ).pack(side="left", padx=10)

        ctk.CTkLabel(
            header,
            text="Foto Model Stüdyo",
            font=ctk.CTkFont(size=22, weight="bold")
            ).pack(side="left", padx=10)"""

    # ---------------- Tabs ----------------
    def create_tabs(self):
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # ---------------- Selection Tab ----------------
        selection_tab = self.tabs.add("Seçimler")
        self.selection_tab = SelectionTab(self, selection_tab)

        # -------- link creating tab ---------
        # self.create_link_tab()
        link_tab = self.tabs.add("Link Oluştur")
        self.link_tab = LinkTab(self, link_tab)

        # ---------------- Upload Tab ----------------
        upload_tab = self.tabs.add("Şablon Yükleme")
        
        self.upload_tab = UploadTab(self, upload_tab)

        self.tabs.add("Log")
        
    # ---------------- Log Tab ----------------
    def create_log_tab(self):
        tab = self.tabs.tab("Log")

        self.log_area = ctk.CTkTextbox(
            tab,
            font=("Consolas", 11)
        )
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, message):
        self.log_area.insert("end", f"{message}\n")
        self.log_area.see("end")


if __name__ == "__main__":
    app = FotoModelApp()
    app.mainloop()