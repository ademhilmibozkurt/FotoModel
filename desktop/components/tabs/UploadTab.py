import os
import threading
import tkinter as tk
import customtkinter as ctk
from io import BytesIO
from PIL import Image, ImageOps
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed

from components.tabs.Fetch import FetchOps
from database import SupabaseDB

class UploadTab:
    def __init__(self, app, tab):
        self.app = app
        self.tab = tab

        self.fetchOps = FetchOps(self, app)

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
            command=self.upload_images_ui_wspinner
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
                target=self.upload_templates_todb,
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
    """def __init__(self, app, tab):
        self.app = app
        self.tab = tab

        self.supabase = SupabaseDB()
        self.phop     = PhotoOperations()

        self.images   = []
        self.image_paths = []
        self.template_widgets = []

        self.CARD_WIDTH  = 299
        self.CARD_HEIGHT = 168
        self.CARD_PAD    = 20
        self.COLS = 4

        self.templates_ready = False

        # for lazy loading
        self.gallery_mode = "None"
        # self._current_cols   = None
        self.template_cards = []
        self.pil_cache = {}
        self.ctk_cache = {}
        self.visible_range = (0, 0)
        
        # limit the number of parallel operations
        self.UPLOAD_LIMIT = 3
        self.upload_semaphore = threading.Semaphore(self.UPLOAD_LIMIT)

        self.DOWNLOAD_LIMIT = 10
        self.download_semaphore = threading.Semaphore(self.DOWNLOAD_LIMIT)
        self.download_executor = ThreadPoolExecutor(max_workers=10)

        self.create_ui()

    def create_ui(self):
        # top of the upload tab
        top_bar = ctk.CTkFrame(self.tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkButton(
            top_bar,
            text="📂 Görselleri Yükle",
            command=self.upload_images_ui_wspinner
        ).pack(side="left", padx=(0,10))

        self.btnGetTemplates = ctk.CTkButton(
            top_bar,
            text="Şablonları Getir",
            command=self.fetch_templates
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
                target=self.upload_templates_todb,
                daemon=True
            ).start())
        self.btnSubmit.pack(side="left")
        self.switch_button(self.btnSubmit, "normal")
        
        self.btnDelete = ctk.CTkButton(
            bottom_bar,
            text="🗑 Seçilenleri Sil",
            fg_color="#B91C1C",
            hover_color="#7F1D1D",
            command=self.delete_selected_templates
        )
        self.btnDelete.pack(side="right")
        self.switch_button(self.btnDelete, "disabled")

        # scroll with mouse
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.update_visible()

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Configure>", lambda e: self.update_visible())
        self.preview_frame.bind("<Configure>",lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    # button disabling for prevent conflicts
    def switch_button(self, btn, state="disabled"):
        if not btn:
            return
        btn.configure(state=state)"""

    # upload to ui 
    def upload_images_ui_wspinner(self):
        self.app.spinner.run_with_spinner(
            task=lambda:self.upload_images_tab(),
            loading_text="Yükleniyor..."
        )
        # clean the screen for futher uploads
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self.images.clear()
        self.switch_button(self.btnSubmit, "normal")
        self.switch_button(self.btnDelete, "disabled")

    # upload template photos to supabase storage
    def upload_images_tab(self):
        self.gallery_mode = "upload"
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.images.clear()
        self.image_paths.clear()
        self.template_cards.clear()
        self.templates_ready = False
        self.image_cache = {}

        paths = filedialog.askopenfilenames(
            title="Şablon Seç",
            filetypes=[("Images", "*.jpg *.png *.webp *.avif")]
        )
        self.image_paths.extend(paths)

        try:
            for path in paths:
                # caching - refactor code below
                if path not in self.image_cache:
                    img = Image.open(path)
                    img = ImageOps.contain(img, (self.CARD_WIDTH, self.CARD_HEIGHT), Image.LANCZOS)
                    self.image_cache[path] = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                    
                ctk_img = self.image_cache[path]
                frame = ctk.CTkFrame(self.preview_frame, width=self.CARD_WIDTH, height=self.CARD_HEIGHT, corner_radius=12)
                # content on the frame fixed
                frame.grid_propagate(False)

                lbl = ctk.CTkLabel(frame, image=ctk_img, text="")
                lbl.image = ctk_img
                lbl.pack(pady=(6,4))

                ctk.CTkLabel(
                    frame,
                    text=os.path.basename(path),
                    font=("Segoe UI", 11),
                    bg_color="#111827",
                    wraplength=self.CARD_WIDTH -10,
                    justify="center",
                    anchor="center"
                ).pack(padx=5, pady=(2, 6))
        
                self.template_cards.append(frame)

            self.templates_ready = True
            # self.app.after(50, self.relayout_gallery)
            self.update_visible()
        
            print(f"Yüklendi: {path}")

        except Exception as e:
            print(f"HATA: {e}")

    # upload to db
    def upload_templates_todb(self):
        self.app.after(0, self.app.spinner.show_spinner)
        threading.Thread(
            target=self._upload_worker,
            daemon=True
        ).start()

        self.switch_button(self.btnSubmit)
        self.switch_button(self.btnGetTemplates, "normal")
        
        self.app.after(0, self._clear_preview)

    def _clear_preview(self):
        # clean the screen for futher uploads
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self.images.clear()
        self.image_paths.clear()

    def _upload_worker(self): 
        errors = self.upload_templates_parallel(self.image_paths)
        if errors:
            messagebox.showerror(
                "Upload Hataları",
                "\n".join(errors[:5])
            )
        
        self.app.after(0, self.app.spinner.hide_spinner)

    def upload_templates_parallel(self, paths: list):
        if not paths:
            return
        
        errors = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self.upload_pair, path): path
                for path in paths
            }

            for future in as_completed(futures):
                err = future.result()
                if err:
                    errors.append(err)
        
        return errors

    def upload_pair(self, path):
        try:
            with self.upload_semaphore:
                supabase = SupabaseDB()
                supabase.upload_template_todb(path, False)
                supabase.upload_template_todb(path, True)
        except Exception as e:
            return str(e)