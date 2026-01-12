import os
import threading
import tkinter as tk
import customtkinter as ctk
from io import BytesIO
from PIL import Image, ImageOps
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed

from database import SupabaseDB
from photoOperations import PhotoOperations

class UploadTab:
    def __init__(self, app, tab):
        self.app = app
        self.tab = tab

        self.supabase = SupabaseDB()
        self.phop     = PhotoOperations()

        self.images   = []
        self.image_paths = []
        self.template_widgets = []

        self.COLS = 4

        # responsive columns
        # self.CARD_WIDTH  = 268
        # self.CARD_HEIGHT = 151
        # self.CARD_PAD    = 25
        # self.MIN_COLS    = 2
        self.templates_ready = False

        # for lazy loading
        self.gallery_mode = "None"
        # self._current_cols   = None
        self.template_cards = []
        self.pil_cache = {}
        self.ctk_cache = {}
        self.visible_range = (0, 0)
        
        # self.MAX_VISIBLE = 40
        # self.BUFFER = 12

        # limit the number of parallel operations
        self.UPLOAD_LIMIT = 3
        self.upload_semaphore = threading.Semaphore(self.UPLOAD_LIMIT)

        self.DOWNLOAD_LIMIT = 4
        self.download_semaphore = threading.Semaphore(self.DOWNLOAD_LIMIT)

        # resize renderer binding  
        # self.app.bind("<Configure>", self.on_window_resize)

        self.create_ui()

    # for calling render_gallery() multiple times
    """def on_window_resize(self, event):
        if not self.templates_ready or event.widget != self.app:
            return

        if hasattr(self, "_resize_job"):
            self.app.after_cancel(self._resize_job)

        self._resize_job = self.app.after(80, self.relayout_gallery)"""

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

        self.canvas = tk.Canvas(content_frame, bg="#1f2937", highlightthickness=0)
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
        btn.configure(state=state)

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
                    img = ImageOps.contain(img, (268, 151), Image.LANCZOS)
                    self.image_cache[path] = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                    
                ctk_img = self.image_cache[path]
                frame = ctk.CTkFrame(self.preview_frame, width=268, height=151, corner_radius=12)
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
                    wraplength=258,
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

    # ---- template fetching ------- fetch photo list from db
    def fetch_templates(self, folder="thumbs"):
        if getattr(self, "templates_loading", False):
            return
        
        self.templates_loading = True
        self.switch_button(self.btnDelete, "normal")
        self.switch_button(self.btnGetTemplates, state="disabled")

        threading.Thread(
            target=self._fetch_templates_worker,
            args=(folder,),
            daemon=True
        ).start()

    def _fetch_templates_worker(self, folder):
        self.app.after(0, self.app.spinner.show_spinner)
        self.switch_button(self.btnSubmit, "disabled")
        try:
            with self.download_semaphore:   
                templates = self.supabase.fetch_templates_fromdb(folder)
                filenames = [t["name"] for t in templates]

                self.app.after(0, lambda: self.show_templates(filenames))
        except Exception as e:
            self.app.after(0, lambda:messagebox.showerror("HATA: ", str(e)))

        finally:
            self.app.after(0, self.app.spinner.hide_spinner)
            self.templates_loading = False

    # download and show fetched list
    def show_templates(self, filenames):
        self.gallery_mode = "fetch"

        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.template_cards.clear()
        self.templates_ready = False

        for filename in filenames:
            frame = ctk.CTkFrame(
                self.preview_frame,
                width=268,
                height=151,
                corner_radius=12
            )
            frame.grid_propagate(False)

            frame.filename = filename
            frame.selected = False
            frame.loaded   = False
            
            lbl = ctk.CTkLabel(frame, text="Yükleniyor...")
            lbl.pack(expand=True)

            frame.img_label = lbl

            frame.bind("<Button-1>", lambda e, f=frame: self.toggle_select(f))
            lbl.bind("<Button-1>", lambda e, f=frame: self.toggle_select(f))

            self.template_cards.append(frame)

        self.templates_ready = True
        # self.relayout_gallery()
        self.visible_range = (-1,-1)
        self.app.after(200, self.update_visible)
        self.app.after(600, self.update_visible)

    def toggle_select(self, frame):
        frame.selected = not frame.selected
        frame.configure(border_color="#3b82f6" if frame.selected else "#111827", border_width=2)

    """def relayout_gallery(self):
        if not self.templates_ready:
            return 
        
        if not self.preview_frame.winfo_exists():
            return
        
        width = self.preview_frame.winfo_width()
        if width <= 1:
            self.app.after(50, self.relayout_gallery)
            return

        cols = max(self.MIN_COLS, width // (self.CARD_WIDTH + self.CARD_PAD))

        self._current_cols = cols
        self.visible_range = (-1, -1)
        self.update_visible()"""

    def update_visible(self):
        if not self.templates_ready: # or not self._current_cols:
            return
        
        # upload mode -> show everything
        if self.gallery_mode == "upload":
            for i, frame in enumerate(self.template_cards):
                if not frame.winfo_exists():continue

                r = i // self.COLS # self._current_cols
                c = i % self.COLS # self._current_cols
                frame.grid(row=r, column=c, padx=15, pady=15)
            return

        # fetch mode -> lazy loading
        start, end = self.get_visible_indices()
        if (start, end) == self.visible_range:
            return

        self.visible_range = (start, end)

        if self.gallery_mode == "fetch":
            for i, frame in enumerate(self.template_cards):
                if not frame.winfo_exists():continue

                r = i // self.COLS # self._current_cols
                c = i % self.COLS # self._current_cols
                frame.grid(row=r, column=c, padx=15, pady=15)

                if start <= i < end and not frame.loaded:
                    self.load_image_async(frame)
                else:
                    pass
        
        self.preview_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # calculate visible area
    def get_visible_indices(self):
        y1 = self.canvas.canvasy(0)
        y2 = y1 + self.canvas.winfo_height()

        # row_h     = self.CARD_HEIGHT + self.CARD_PAD
        row_h = 200
        start_row = max(0, int(y1 // row_h) - 1)
        end_row   = int(y2 // row_h) +4

        start = start_row * self.COLS # self._current_cols
        end   = end_row * self.COLS # self._current_cols

        return start, min(end, len(self.template_cards))
    
    # loading images with threading
    def load_image_async(self, frame):
        fn = frame.filename
        # if cache exist attach it
        if fn in self.ctk_cache:
            self.app.after(0, lambda: self.attach_image(frame))
            return
            
        def worker():
            res = self.supabase.download_templates_fromdb(fn)
            img = Image.open(BytesIO(res))
            img = ImageOps.contain(img, (268, 151), Image.LANCZOS)

            self.pil_cache[fn] = img
            self.ctk_cache[fn] = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(img.width, img.height)
            )

            self.app.after(0, lambda: self.attach_image(frame))

        threading.Thread(target=worker, daemon=True).start()

    # attach image to label
    def attach_image(self, frame):
        if frame.loaded:
            return

        img = self.ctk_cache.get(frame.filename)
        if not img:
            return

        frame.img_label.destroy()

        lbl       = ctk.CTkLabel(frame, image=img, text="")
        lbl.image = img
        lbl.pack(padx=10, pady=(10,5))

        lbl.bind("<Button-1>", lambda e, f=frame: self.toggle_select(f))

        frame.loaded = True

    # delete selected templates from supabase storage
    def delete_selected_templates(self):
        selected = [
            frame.filename
            for frame in self.template_cards
                if getattr(frame, "selected", False)
        ]

        if not selected:
            messagebox.showinfo("Bilgi", "Silinecek şablon seçilmedi.")
            return

        threading.Thread(
            target=self.delete_templates_worker,
            args=(selected,),
            daemon=True
        ).start()

        self.switch_button(self.btnDelete, "disabled")

    def delete_templates_worker(self, selected):
        self.app.after(0, self.app.spinner.show_spinner)
        try:
            for filename in selected:
                self.supabase.delete_template_fromdb(filename)

            self.app.after(10, self.fetch_templates)
            print("DELETE RESPONSE: Deleted!")

        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror("HATA: ", str(e)))

        finally:
            self.app.after(50, self.app.spinner.hide_spinner)