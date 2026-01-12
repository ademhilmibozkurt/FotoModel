import time
import json
import threading
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from io import BytesIO
from PIL import Image, ImageOps
from threading import Semaphore

from database import SupabaseDB

class SelectionTab:
    def __init__(self, app, tab):
        self.app = app
        self.tab = tab
        self.supabase = SupabaseDB()

        self.CARD_WIDTH = 268
        self.CARD_HEIGHT = 151
        self.COLS = 5

        self.search_var = tk.StringVar()
        self.tree = None
        self.all_data = []
        self.grid_cells = []
        self.resize_job = None
        self.selected_template_cache = {}

        self.create_ui()

        self.download_semaphore = Semaphore(3)

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
            self.tree.column(col, width=50)

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

        self.open_selection_detail(record)
        
    # selected templates window
    def open_selection_detail(self, record):
        self.window = ctk.CTkToplevel(self.app)
        self.window.title("Seçilen Fotoğraflar")
        
        #self.window.geometry("1600x1000")
        self.app.center_window(1600, 1000, self.window)

        header = ctk.CTkFrame(self.window)
        header.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(header, text=f"İsim   : {record['İsim']}").pack(anchor="w")
        ctk.CTkLabel(header, text=f"Telefon: {record['Telefon']}").pack(anchor="w")
        ctk.CTkLabel(header, text=f"Tarih  : {record['Tarih']}").pack(anchor="w")

        self.scroll = ctk.CTkScrollableFrame(self.window)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        selected = record["Seçimler"]
        if isinstance(selected, str):
            selected = json.loads(selected)

        self.selected_filenames = selected
        self.loaded_indices     = set()

        self.grid_cells = [None] * len(self.selected_filenames)
        self.placeholder_frames = []

        # for responsive screen size
        # self.window.bind("<Configure>", self.on_resize)

        # lazy loading binding
        self.scroll._parent_canvas.bind("<Configure>", lambda e: self.load_visible_images())

        self._create_placeholders()
        self.app.after(100, self.load_visible_images)

    # for prevent fixed scroll to load new images
    def _create_placeholders(self):
        for i in range(len(self.selected_filenames)):
            cell = ctk.CTkFrame(self.scroll, width=self.CARD_WIDTH, height=self.CARD_HEIGHT)
            cell.grid_propagate(False)

            r = i // self.COLS
            c = i % self.COLS
            cell.grid(row=r, column=c, padx=10, pady=10)

            self.placeholder_frames.append(cell)
            # self.grid_cells.append(None)

        # self.reflow_grid()

    """def on_resize(self, event):
        if self.resize_job:
            self.app.after_cancel(self.resize_job)

        self.resize_job = self.app.after(80, self.reflow_grid)"""
    
    def load_visible_images(self):
        if not self.scroll.winfo_exists():
            return
        
        start, end = self.get_visible_indices()
        for i in range(start, end):
            if i in self.loaded_indices:
                continue

            self.loaded_indices.add(i)
            filename = self.selected_filenames[i]

            threading.Thread(
                target=self._load_single_image,
                args=(filename, i),
                daemon=True
            ).start()

    def get_visible_indices(self):
        canvas = self.scroll._parent_canvas

        y1 = canvas.canvasy(0)
        y2 = y1 + canvas.winfo_height()

        row_h = 171
        # cols = max(1, canvas.winfo_width() // self.CARD_WIDTH)

        start_row = max(0, int(y1 // row_h) - 1)
        end_row   = int(y2 // row_h) + 1

        start = start_row * self.COLS # cols
        end   = end_row * self.COLS # cols

        return start, min(end, len(self.selected_filenames))

    def _load_single_image(self, filename, index):
        with self.download_semaphore:
            try:
                img = self.supabase.download_templates_fromdb(filename, folder="original")
                if not img:
                    return
                
                img = Image.open(BytesIO(img))
                img = ImageOps.contain(img, (self.CARD_WIDTH, self.CARD_HEIGHT), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)

                self.app.after(0, lambda: self._attach_image(ctk_img, index))

            except Exception as e:
                print(f"DOWNLOAD ERROR {filename} -> {e}")            

    def _attach_image(self, ctk_img, index):
        if not self.scroll.winfo_exists():
            return 
        
        placeholder = self.placeholder_frames[index]

        for w in placeholder.winfo_children():
            w.destroy()

        lbl  = ctk.CTkLabel(placeholder, image=ctk_img, text="")
        lbl.image = ctk_img
        lbl.pack()
        
        # self.grid_cells.append(placeholder)
    
    """def reflow_grid(self):
        if not self.grid_cells:
            return

        container_width = self.scroll.winfo_width()
        if container_width <= 1:
            self.app.after(50, self.reflow_grid)
            return

        photo_size = 288
        cols = max(1, container_width // photo_size)

        for index, cell in enumerate(self.grid_cells):
            r = index // cols
            c = index % cols

            cell.grid(row=r, column=c, padx=10, pady=10)"""