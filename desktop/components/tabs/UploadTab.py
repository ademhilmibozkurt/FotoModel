import threading
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from components.tabs.Upload import UploadOps
from components.tabs.Fetch import FetchOps

class UploadTab:
    def __init__(self, app, tab):
        self.app = app
        self.tab = tab

        self.uploadOps = UploadOps(self, app)
        self.fetchOps  = FetchOps(self, app)

        self.images   = []
        self.image_paths = []

        self.CARD_WIDTH  = 299
        self.CARD_HEIGHT = 168
        self.CARD_PAD    = 20
        self.COLS = 4

        self.templates_ready = False

        # for lazy loading
        self.gallery_mode = "None"
        # self._current_cols   = None
        self.template_cards = []
        
        # limit the number of parallel operations
        self.UPLOAD_LIMIT = 3
        self.upload_semaphore = threading.Semaphore(self.UPLOAD_LIMIT)

        self.create_ui()

    def create_ui(self):
        # top of the upload tab
        top_bar = ctk.CTkFrame(self.tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkButton(
            top_bar,
            text="📂 Görselleri Yükle",
            command=self.uploadOps.upload_images_ui_wspinner
        ).pack(side="left", padx=(0,10))

        self.btnGetTemplates = ctk.CTkButton(
            top_bar,
            text="Şablonları Getir",
            command=self.fetchOps.fetch_templates
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
            command=self.fetchOps.delete_selected_templates
        )
        self.btnDelete.pack(side="right")
        self.switch_button(self.btnDelete, "disabled")

        # scroll with mouse
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.fetchOps.update_visible()

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Configure>", lambda e: self.fetchOps.update_visible())
        self.preview_frame.bind("<Configure>",lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    # button disabling for prevent conflicts
    def switch_button(self, btn, state="disabled"):
        if not btn:
            return
        btn.configure(state=state)