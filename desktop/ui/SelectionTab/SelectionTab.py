import time
import json
import threading
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from io import BytesIO
from PIL import Image, ImageOps
from threading import Semaphore

from infra.database import SupabaseDB
from services.SelectionOps import SelectionOps

class SelectionTab:
    def __init__(self, app, tab):
        self.app = app
        self.tab = tab

        self.supabase     = SupabaseDB()
        self.selectionOps = SelectionOps(self)

        self.CARD_WIDTH  = 384
        self.CARD_HEIGHT = 216
        self.CARD_PAD    = 20
        self.COLS = 3
        self.window_width = 1600
        self.window_height = 900

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

        self.search_var.trace_add("write", self.selectionOps.filter_tree)

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
        self.tree.bind("<Double-1>", self.selectionOps.on_tree_double_click)

        # is_completed state toggle
        self.tree.bind("<Button-1>", self.selectionOps.on_tree_single_click)

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
        self.selectionOps.refresh_tree(self.all_data)
        print(f"Seçimler getirildi ({time.strftime('%H:%M:%S')})")
        
    # selected templates window
    def open_selection_detail(self, record):
        self.window = ctk.CTkToplevel(self.app)
        self.window.title("Seçilen Fotoğraflar")
        
        self.app.center_window(self.window_width, self.window_height, self.window)

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
            cell.grid(row=r, column=c, padx=self.CARD_PAD+20, pady=self.CARD_PAD, sticky="n")
            
            self.placeholder_frames.append(cell)
    
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

        row_h = self.CARD_HEIGHT + self.CARD_PAD

        start_row = max(0, int(y1 // row_h) - 1)
        end_row   = int(y2 // row_h) + 1

        start = start_row * self.COLS
        end   = end_row * self.COLS 

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
        lbl.pack(expand=True, fill="both")