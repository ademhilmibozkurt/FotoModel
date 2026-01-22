import threading
import tkinter as tk
import customtkinter as ctk

from infra.database import SupabaseDB

class LinkTab:
    # ready link -> fcc684f0-97fc-4e4c-929a-dfeb3ccb1909
    def __init__(self, app, tab):
        self.app = app
        self.tab = tab
        self.supabase = SupabaseDB()

        self.create_link_tab()

    def create_link_tab(self):
        container = ctk.CTkFrame(self.tab, fg_color="transparent")
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
        self.app.after(0, self.app.spinner.show_spinner)
        self.link_var.set("Link oluşturuluyor...")

        threading.Thread(
            target=self.create_link_worker,
            daemon=True
        ).start()

    def create_link_worker(self):
        try:
            link = self.supabase.get_link()
            self.app.after(0, lambda: self.link_var.set(link))
        except Exception as e:
            self.app.after(0, lambda: self.link_var.set(f"HATA: {e}"))

        finally:
            self.app.after(0, self.app.spinner.hide_spinner)

    def copy_link(self):
        link = self.link_var.get()
        if not link:
            return

        self.app.clipboard_clear()
        self.app.clipboard_append(link)
        self.app.update()

        self.link_var.set("✅ Kopyalandı")
        self.app.after(1500, lambda: self.link_var.set(link))