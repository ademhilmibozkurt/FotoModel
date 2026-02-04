import threading
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from services.UploadOps import UploadOps
from services.DeleteOps import DeleteOps

from ui.UploadTab.Fetch import Fetch

class UploadTab:
    def __init__(self, app, tab):
        self.app = app
        self.tab = tab

        self.fetch = Fetch(self, self.app)

        self.uploadOps = UploadOps(self, app)
        self.deleteOps = DeleteOps(self.fetch, self, app)

        self.create_ui()

    def create_ui(self):
        # top of the upload tab
        top_bar = ctk.CTkFrame(self.tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkButton(
            top_bar,
            text="📂 Görselleri Yükle",
            command=self.uploadOps.upload_images
        ).pack(side="left", padx=(0,10))

        self.btnGetTemplates = ctk.CTkButton(
            top_bar,
            text="Şablonları Getir",
            command=self.fetch.fetch_templates
        )
        self.btnGetTemplates.pack(side="left")

        # content section of the upload tab
        content_frame = ctk.CTkFrame(self.tab)
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.canvas = tk.Canvas(content_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.preview_frame = ctk.CTkFrame(self.canvas)
        self.canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")

        # submit, fetch and delete buttons
        bottom_bar = ctk.CTkFrame(self.tab, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=15, pady=(5, 15))

        self.btnSubmit = ctk.CTkButton(
            bottom_bar,
            text="Onayla",
            command=lambda: threading.Thread(
                target=self.uploadOps.upload_templates_todb,
                daemon=True
            ).start())
        self.btnSubmit.pack(side="left")
        self.switch_button(self.btnSubmit, "normal")
        
        self.btnDelete = ctk.CTkButton(
            bottom_bar,
            text="🗑 Seçilenleri Sil",
            fg_color="#B91C1C",
            hover_color="#7F1D1D",
            command=self.deleteOps.delete_selected_templates
        )
        self.btnDelete.pack(side="right")
        self.switch_button(self.btnDelete, "disabled")

        # scroll with mouse
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.fetch.update()

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Configure>", lambda e: self.fetch.update())
        self.preview_frame.bind("<Configure>",lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    # button disabling for prevent conflicts
    def switch_button(self, btn, state="disabled"):
        if not btn:
            return
        btn.configure(state=state)