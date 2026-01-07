import os
import time
import json
import threading
from io import BytesIO
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps
from database import SupabaseDB
from photoOperations import PhotoOperations
from concurrent.futures import ThreadPoolExecutor, as_completed

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

        self.supabase = SupabaseDB()
        self.phop     = PhotoOperations()
        self.all_data = []
        self.images   = []
        self.image_paths = []
        self.template_widgets = []

        self.selected_template_cache = {}
        self.grid_cells = []
        self.resize_job = None

        # responsive columns
        self.CARD_WIDTH  = 268
        self.CARD_HEIGHT = 151
        self.CARD_PAD    = 25
        self.MIN_COLS    = 2
        self.templates_ready = False

        # resize renderer binding  
        self.bind("<Configure>", self.on_window_resize)
        # listen canvas size changes
        self.preview_frame.bind("<Configure>", lambda e: self.relayout_gallery())

        # for lazy loading
        self.gallery_mode = "None"
        self._current_cols   = None
        self.template_cards = []
        self.pil_cache = {}
        self.ctk_cache = {}
        self.visible_range = (0, 0)
        self.MAX_VISIBLE = 40
        self.BUFFER = 12

        # limit the number of parallel operations
        self.UPLOAD_LIMIT = 3
        self.upload_semaphore = threading.Semaphore(self.UPLOAD_LIMIT)

        # for calling render_gallery() multiple times
    def on_window_resize(self, event):
        if not self.templates_ready or event.widget != self:
            return

        if hasattr(self, "_resize_job"):
            self.after_cancel(self._resize_job)

        self._resize_job = self.after(80, self.relayout_gallery)

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

        self.create_selection_tab()
        self.create_link_tab()
        self.create_upload_tab()

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
        def worker():
            try:
                result = task()
                if on_success:
                    self.after(0, lambda: on_success(result))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Hata", str(e)))
                self.after(0, lambda: self.log(f"HATA: {e}"))
            finally:
                self.after(0, self.hide_spinner)

        self.show_spinner(loading_text)
        threading.Thread(target=worker, daemon=True).start()

    # ---------------- Selection Tab ----------------
    def create_selection_tab(self):
        tab = self.tabs.tab("Seçimler")

        search_frame = ctk.CTkFrame(tab)
        search_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(search_frame, text="Ara:").pack(side="left", padx=5)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_tree)

        ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=300
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            search_frame,
            text="Güncelle",
            command=self.load_supabase_data
        ).pack(side="right", padx=5)

        # ---- TreeView (ttk) ----
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#1f2937",
            foreground="white",
            fieldbackground="#1f2937",
            rowheight=28
        )
        style.configure("Treeview.Heading", background="#111827", foreground="white")

        self.tree = ttk.Treeview(tab)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # open new window with double click
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # is_completed state toggle
        self.tree.bind("<Button-1>", self.on_tree_single_click)

    def load_supabase_data(self):
        try:
            self.run_with_spinner(
                task=self.supabase.fetch_template_selection,
                on_success=self.on_supabase_loaded,
                loading_text="Veriler getiriliyor..."
            )
        except Exception as e:
            messagebox.showerror("Veritabanı Hatası", str(e))
            self.log(f"HATA: {e}")

    def on_supabase_loaded(self, data):
        self.all_data = data
        self.refresh_tree(self.all_data)
        self.log(f"Seçimler getirildi ({time.strftime('%H:%M:%S')})")

    def refresh_tree(self, data):
        self.tree.delete(*self.tree.get_children())

        if not data:
            return

        columns = list(data[0].keys())

        # add is_completed state
        if "Durum" not in columns:
            columns.insert(0, "Durum")

        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80)

        # for show selected templates in new window
        self.tree_record_map = {}
        for row in data:
            completed = row.get("is_completed", False)
            status_text = "✔" if completed else "⬜"
            
            values = [status_text] + list(row.values())

            item_id = self.tree.insert("", "end", values=values)
            self.tree_record_map[item_id] = row

    def filter_tree(self, *args):
        query = self.search_var.get().lower()

        if not query:
            self.refresh_tree(self.all_data)
            return

        filtered = [
            row for row in self.all_data
            if any(query in str(v).lower() for v in row.values())
        ]

        self.refresh_tree(filtered)

    # on single click update is_completed state
    def on_tree_single_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        if column != "#1":
            return

        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        values = list(self.tree.item(row_id, "values"))
        current = values[0]

        new_value = "✔" if current == "⬜" else "⬜"
        values[0] = new_value
        self.tree.item(row_id, values=values)

        record = self.tree_record_map.get(row_id)
        if record:
            self.supabase.update_completed_status(record, new_value == "✔")

    # on double click open new window for show selected images
    def on_tree_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        record = self.tree_record_map.get(item_id)

        if not record:
            return

        self.run_with_spinner(
            task=lambda: self.open_selection_detail(record),
            loading_text="Yükleniyor..."
        )
        
    # !! fotoğraflar grid yapısında yan yana gözükmeli altalta gözüküyor !!
    # selected templates window
    def open_selection_detail(self, record):
        window = ctk.CTkToplevel(self)
        window.title("Seçilen Fotoğraflar")
        window.geometry("1400x800")

        header = ctk.CTkFrame(window)
        header.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(header, text=f"İsim   : {record['İsim']}").pack(anchor="w")
        ctk.CTkLabel(header, text=f"Telefon: {record['Telefon']}").pack(anchor="w")
        ctk.CTkLabel(header, text=f"Tarih  : {record['Tarih']}").pack(anchor="w")

        selected = record["Seçimler"]
        if isinstance(selected, str):
            selected = json.loads(selected)

        threading.Thread(
            target=self.render_selected_photos,
            args=(window, selected),
            daemon=True
        ).start()

        # for responsive screen size
        window.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        if self.resize_job:
            self.after_cancel(self.resize_job)

        self.resize_job = self.after(80, self.reflow_grid)

    # get images from db - this code below doing same job like show_templates_as_image
    def render_selected_photos(self, parent, selected_templates):
        self.scroll = ctk.CTkScrollableFrame(parent)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.grid_cells.clear()

        for filename in selected_templates:
            if filename not in self.selected_template_cache:
                img = self.supabase.download_templates_fromdb(filename, folder="original")

                if img == None:
                    continue
                else:
                    img = Image.open(BytesIO(img))
                    img = ImageOps.contain(img, (268, 151), Image.LANCZOS)

                    ctk_img = ctk.CTkImage(img, size=img.size)
                    self.selected_template_cache[filename] = ctk_img

            cell = ctk.CTkFrame(self.scroll)
            label = ctk.CTkLabel(cell, image=self.selected_template_cache[filename], text="")
            label.image = self.selected_template_cache[filename]
            label.pack()

            self.grid_cells.append(cell)

        self.reflow_grid()
    
    def reflow_grid(self):
        if not self.grid_cells:
            return

        container_width = self.scroll.winfo_width()
        if container_width <= 1:
            return

        photo_size = 268
        max_columns = max(1, container_width // photo_size)

        for index, cell in enumerate(self.grid_cells):
            r = index // max_columns
            c = index % max_columns

            cell.grid(row=r, column=c, padx=10, pady=10, sticky="n")

    # ---------------- Upload Tab ----------------
    def create_upload_tab(self):
        tab = self.tabs.tab("Şablon Yükleme")

        # top of the upload tab
        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
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
        content_frame = ctk.CTkFrame(tab)
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.canvas = tk.Canvas(content_frame, bg="#1f2937", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.preview_frame = ctk.CTkFrame(self.canvas)
        self.canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")

        self.preview_frame.bind("<Configure>",lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # scroll with mouse
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # submit, fetch and delete buttons
        bottom_bar = ctk.CTkFrame(tab, fg_color="transparent")
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

    # button disabling for prevent conflicts
    def switch_button(self, btn, state="disabled"):
        if not btn:
            return
        btn.configure(state=state)

    # upload to ui 
    def upload_images_ui_wspinner(self):
        self.run_with_spinner(
            task=lambda:self.upload_images_tab(),
            loading_text="Yükleniyor..."
        )
        # clean the screen for futher uploads
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self.images.clear()
        self.switch_button(self.btnSubmit, "normal")
        self.switch_button(self.btnDelete, "disabled")

    # !!! upload kısmında fotolar gelmiyor fetch yapınca sadece bir foto geliyor
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
                    wraplength=self.CARD_WIDTH - 10,
                    justify="center",
                    anchor="center"
                ).pack(padx=5, pady=(2, 6))
        
                self.template_cards.append(frame)

            self.templates_ready = True
            self.after_idle(self.relayout_gallery)
        
            self.log(f"Yüklendi: {path}")

        except Exception as e:
            self.log(f"HATA: {e}")

    # upload to db
    def upload_templates_todb(self):
        threading.Thread(
            target=self._upload_worker,
            daemon=True
        ).start()

        # clean the screen for futher uploads
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self.images.clear()
        self.image_paths.clear()
        self.switch_button(self.btnSubmit)
        self.switch_button(self.btnGetTemplates, "normal")

    def _upload_worker(self):
        self.show_spinner()
        errors = self.upload_templates_parallel(self.image_paths)
        self.after(0, self.hide_spinner)

        if errors:
            messagebox.showerror(
                "Upload Hataları",
                "\n".join(errors[:5])
            )

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
        self.show_spinner()
        self.switch_button(self.btnSubmit, "disabled")
        try:
            templates = self.supabase.fetch_templates_fromdb(folder)
            filenames = [t["name"] for t in templates]

            self.after(0, lambda: self.show_templates(filenames))
        except Exception as e:
            self.after(0, lambda:messagebox.showerror("HATA: ", str(e)))

        finally:
            self.after(0, self.hide_spinner)
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
                width=self.CARD_WIDTH,
                height=self.CARD_HEIGHT,
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
        self.relayout_gallery()
        self.update_visible()

    def toggle_select(self, frame):
        frame.selected = not frame.selected
        frame.configure(border_color="#3b82f6" if frame.selected else "#111827", border_width=2)

    def relayout_gallery(self):
        if not self.templates_ready:
            return 
        
        if not self.canvas.winfo_exists():
            return
        
        width = self.canvas.winfo_width()
        if width <= 1:
            self.after(50, self.relayout_gallery)
            return

        cols = max(self.MIN_COLS, width // (self.CARD_WIDTH + self.CARD_PAD))

        self._current_cols = cols
        self.visible_range = (-1, -1)
        self.update_visible()

    def update_visible(self):
        if not self.templates_ready or not self._current_cols:
            return
        
        # upload mode -> show everything
        if self.gallery_mode == "upload":
            for i, frame in enumerate(self.template_cards):
                if not frame.winfo_exists():continue

                r = i // self._current_cols
                c = i % self._current_cols
                frame.grid(row=r, column=c, padx=15, pady=15)
            return

        # fetch mode -> lazy loading
        start, end = self.get_visible_indices()
        if (start, end) == self.visible_range:
            return

        self.visible_range = (start, end)

        for i, frame in enumerate(self.template_cards):
            if not frame.winfo_exists():continue

            if start <= i < end:
                r = i // self._current_cols
                c = i % self._current_cols
                frame.grid(row=r, column=c, padx=15, pady=15)

            if self.gallery_mode == "fetch":
                if not frame.loaded:
                    self.load_image_async(frame)

            else:
                frame.grid_forget()
        
        self.preview_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # calculate visible area
    def get_visible_indices(self):
        y1 = self.canvas.canvasy(0)
        y2 = y1 + self.canvas.winfo_height()

        row_h     = self.CARD_HEIGHT + self.CARD_PAD
        start_row = max(0, int(y1 // row_h) - 1)
        end_row   = int(y2 // row_h) +2

        start = start_row * self._current_cols
        end   = end_row * self._current_cols

        return start, min(end, len(self.template_cards))
    
    # loading images with threading
    def load_image_async(self, frame):
        fn = frame.filename
        # if cache exist attach it
        if fn in self.ctk_cache:
            self.after(0, lambda: self.attach_image(frame))
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

            self.after(0, lambda: self.attach_image(frame))

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
        self.after(0, self.show_spinner)
        try:
            for filename in selected:
                self.supabase.delete_template_fromdb(filename)

            self.after(10, self.fetch_templates)
            print("DELETE RESPONSE: Deleted!")

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("HATA: ", str(e)))

        finally:
            self.after(50, self.hide_spinner)

    # -------- link creating tab ---------
    def create_link_tab(self):
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
        self.after(1500, lambda: self.link_var.set(link))

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