import threading
import customtkinter as ctk
from tkinter import messagebox

class Loader:
    def __init__(self, app):
        self.app = app
        self.spinner = None
        self.spinner_label = None
        self.spinner_overlay = None

        self.create_spinner()

    def create_spinner(self):
        self.spinner_overlay = ctk.CTkFrame(
        master=self.app,
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
                self.app.after(0, lambda: on_success(result) if on_success else None)
            except Exception as e:
                err = str(e)
                self.app.after(0, lambda: messagebox.showerror("HATA", err))
                self.app.after(0, lambda: self.log(f"HATA: {err}"))
            finally:
                self.app.after(0, self.hide_spinner)

        self.app.after(0, threading.Thread(target=worker, daemon=True).start())