import os
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

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
        self.create_spinner()

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
        
    # -------------- Spinner --------------
    def create_spinner(self):
        self.spinner_overlay = ctk.CTkFrame(
        self,
        fg_color=("gray90", "#020617"),corner_radius=0)

        self.spinner_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.spinner_overlay.lower()

        self.spinner = ctk.CTkProgressBar(
            self.spinner_overlay,
            mode="indeterminate",
            width=300
        )
        self.spinner.pack(expand=True)

        self.spinner_label = ctk.CTkLabel(
            self.spinner_overlay,
            text="Yükleniyor...",
            font=ctk.CTkFont(size=14)
        )
        self.spinner_label.pack(pady=10)

    def show_spinner(self, text="Yükleniyor..."):
        self.spinner_label.configure(text=text)
        self.spinner_overlay.lift()
        self.spinner.start()

    def hide_spinner(self):
        self.spinner.stop()
        self.spinner_overlay.lower()

    def run_with_spinner(self, task, on_success=None, loading_text="Yükleniyor..."):
        self.show_spinner(loading_text)
        def worker():
            try:
                result = task()
                self.after(0, lambda: on_success(result) if on_success else None)
            except Exception as e:
                err = str(e)
                self.after(0, lambda: messagebox.showerror("HATA", err))
                self.after(0, lambda: self.log(f"HATA: {err}"))
            finally:
                self.after(0, self.hide_spinner)

        threading.Thread(target=worker, daemon=True).start()

    # -------- link creating tab ---------
    """def create_link_tab(self):
        tab = self.tabs.tab("Link Oluştur")

        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(expand=True)

        self.link_btn = ctk.CTkButton(
            container,
            text="🔗 Link Oluştur",
            command=self.create_link,
            width=200,
            height=40
        )
        self.link_btn.pack(pady=(0, 15))

        result_frame = ctk.CTkFrame(container)
        result_frame.pack()

        self.link_var = tk.StringVar(value="")

        self.link_label = ctk.CTkLabel(
            result_frame,
            textvariable=self.link_var,
            wraplength=420,
            text_color="#9ca3af"
        )
        self.link_label.pack(side="left", padx=(10, 5), pady=10)

        self.copy_btn = ctk.CTkButton(
            result_frame,
            text="📋",
            width=40,
            command=self.copy_link
        )
        self.copy_btn.pack(side="left", padx=(5, 10))

    def create_link(self):
        self.show_spinner()
        self.link_var.set("Link oluşturuluyor...")

        threading.Thread(
            target=self.create_link_worker,
            daemon=True
        ).start()

    def create_link_worker(self):
        try:
            link = self.supabase.get_link()
            self.after(0, lambda: self.link_var.set(link))

        except Exception as e:
            self.after(0, lambda: self.link_var.set(f"HATA: {e}"))

        finally:
            self.after(0, self.hide_spinner)

    def copy_link(self):
        link = self.link_var.get()
        if not link:
            return

        self.clipboard_clear()
        self.clipboard_append(link)
        self.update()

        self.link_var.set("✅ Kopyalandı")
        self.after(1500, lambda: self.link_var.set(link))"""

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