import time
import json
import threading
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from io import BytesIO
from PIL import Image, ImageOps

from database import SupabaseDB

class SelectionTab:
    def __init__(self, app, tab):
        self.app = app
        self.tab = tab
        self.supabase = SupabaseDB()

        self.search_var = tk.StringVar()
        self.tree = None
        self.all_data = []
        self.grid_cells = []
        self.resize_job = None
        self.selected_template_cache = {}

        self.create_ui()

    def create_ui(self):
        search_frame = ctk.CTkFrame(self.tab)
        search_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(search_frame, text="Ara:").pack(side="left", padx=5)

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

        self.create_tree()

    def create_tree(self):
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

        self.tree = ttk.Treeview(self.tab)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # open new window with double click
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # is_completed state toggle
        self.tree.bind("<Button-1>", self.on_tree_single_click)

    def load_supabase_data(self):
        try:
            self.app.spinner.run_with_spinner(
                task=self.supabase.fetch_template_selection,
                on_success=self.on_supabase_loaded,
                loading_text="Veriler getiriliyor..."
            )
        except Exception as e:
            print("Veritabanı Hatası", str(e))

    def on_supabase_loaded(self, data):
        self.all_data = data
        self.refresh_tree(self.all_data)
        print(f"Seçimler getirildi ({time.strftime('%H:%M:%S')})")

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

        self.app.spinner.run_with_spinner(
            task=lambda: self.open_selection_detail(record),
            loading_text="Yükleniyor..."
        )
        
    # selected templates window
    def open_selection_detail(self, record):
        window = ctk.CTkToplevel(self.app)
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
            target=self._load_images_worker,
            args=(window, selected),
            daemon=True
        ).start()

        # for responsive screen size
        window.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        if self.resize_job:
            self.app.after_cancel(self.resize_job)

        self.resize_job = self.app.after(80, self.reflow_grid)

    def _load_images_worker(self, window, selected):
        images = []

        for filename in selected:
            img = self.supabase.download_templates_fromdb(filename, folder="original")
            if img:
                img = Image.open(BytesIO(img))
                img = ImageOps.contain(img, (268, 151), Image.LANCZOS)
                images.append((filename, img))

        # !!! return main thread to UI
        self.app.after(0, lambda: self.render_selected_photos(window, images))

    # get images from db - this code below doing same job like show_templates_as_image
    def render_selected_photos(self, parent, images):
        self.scroll = ctk.CTkScrollableFrame(parent)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.grid_cells.clear()

        for filename, img in images:
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