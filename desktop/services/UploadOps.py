import os
import threading
import customtkinter as ctk
from PIL import Image, ImageOps
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed

from infra.database import SupabaseDB

class UploadOps:
    def __init__(self, tab, app):
        self.tab = tab
        self.app = app

        self.images   = []
        self.image_paths = []

        self.CARD_WIDTH  = 299
        self.CARD_HEIGHT = 168
        self.CARD_PAD    = 20
        self.COLS = 4

        self.templates_ready = False
        # for lazy loading
        self.gallery_mode = "None"
        
        self.template_cards = []
        
        self.visible_range = (0, 0)
        
        # limit the number of parallel operations
        self.UPLOAD_LIMIT = 3
        self.upload_semaphore = threading.Semaphore(self.UPLOAD_LIMIT)

    # ------------------- ui kısmını ayır -------------------
    # upload to ui 
    def upload_images_ui_wspinner(self):
        self.app.spinner.run_with_spinner(
            task=lambda:self.upload_images_tab(),
            loading_text="Yükleniyor..."
        )
        # clean the screen for futher uploads
        for widget in self.tab.preview_frame.winfo_children():
            widget.destroy()
        self.images.clear()
        self.tab.switch_button(self.tab.btnSubmit, "normal")
        self.tab.switch_button(self.tab.btnDelete, "disabled")

    # upload template photos to supabase storage
    def upload_images_tab(self):
        self.gallery_mode = "upload"
        for widget in self.tab.preview_frame.winfo_children():
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
                frame = ctk.CTkFrame(self.tab.preview_frame, width=self.CARD_WIDTH, height=self.CARD_HEIGHT, corner_radius=12)
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

    def _clear_preview(self):
        # clean the screen for futher uploads
        for widget in self.tab.preview_frame.winfo_children():
            widget.destroy()
        self.images.clear()
        self.image_paths.clear()

    # ------------------- bu kısım buranın işi üstü ui al --------------------------    
    # upload to db
    def upload_templates_todb(self):
        self.app.after(0, self.app.spinner.show_spinner)
        threading.Thread(
            target=self._upload_worker,
            daemon=True
        ).start()

        self.tab.switch_button(self.tab.btnSubmit)
        self.tab.switch_button(self.tab.btnGetTemplates, "normal")
        
        self.app.after(0, self._clear_preview)

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
        
    # ----------------- !!! bu kısmı böl !!! --------------------------    
    def update_visible(self):
        if not self.templates_ready: # or not self._current_cols:
            return
        
        # upload mode -> show everything
        if self.gallery_mode == "upload":
            for i, frame in enumerate(self.template_cards):
                if not frame.winfo_exists():continue

                r = i // self.COLS # self._current_cols
                c = i % self.COLS # self._current_cols
                frame.grid(row=r, column=c, padx=15, pady=15, sticky="n")
            return