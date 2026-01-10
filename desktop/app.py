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
        # ---------------- Window ----------------
        self.title("Foto Model Studio")
        self.geometry("1400x800")
        self.create_ui()

        # -------------- Spinner --------------
        self.spinner = Loader(self)

    # ---------------- UI ----------------
    def create_ui(self):
        self.create_header()
        self.create_tabs()
        self.create_log_tab()

    # ---------------- Header ----------------
    def create_header(self):
        header = ctk.CTkFrame(self, height=70, corner_radius=0)
        header.pack(fill="x")

        if os.path.exists("logo.jpg"):
            logo_img = Image.open("logo.jpg").resize((50, 50))
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
            ).pack(side="left", padx=10)

    # ---------------- Tabs ----------------
    def create_tabs(self):
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabs.add("Seçimler")
        self.tabs.add("Link Oluştur")
        self.tabs.add("Şablon Yükleme")
        self.tabs.add("Log")

        # ---------------- Selection Tab ----------------
        selection_tab = self.tabs.tab("Seçimler")
        self.selection_tab = SelectionTab(self, selection_tab)

        # -------- link creating tab ---------
        # self.create_link_tab()
        link_tab = self.tabs.tab("Link Oluştur")
        self.link_tab = LinkTab(self, link_tab)

        # ---------------- Upload Tab ----------------
        upload_tab = self.tabs.tab("Şablon Yükleme")
        self.upload_tab = UploadTab(self, upload_tab)


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