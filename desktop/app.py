import os
import time
import threading
from io import BytesIO
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from database import SupabaseDB
from photoOperations import PhotoOperations

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
        self.phop = PhotoOperations()
        self.all_data = []
        self.images = []
        self.image_paths = []
        self.template_widgets = [] 

        # responsive columns
        self.CARD_WIDTH = 225
        self.CARD_HEIGHT = 175
        self.CARD_PAD   = 25
        self.MIN_COLS   = 2
        self.templates_ready = False

        # resize renderer binding  
        self.bind("<Configure>", self.on_window_resize)

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
            self.logo = ImageTk.PhotoImage(logo_img)

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
        self.tabs.add("Şablon Yükleme")
        self.tabs.add("Log")

        self.create_supabase_tab()
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

    
    def start_spinner(self):
        self.spinner.start()
        self.spinner_label.configure(text="İşlem yapılıyor...")
        self.spinner.pack(pady=10)
        self.spinner_label.pack()

    def stop_spinner(self):
        self.spinner.stop()
        self.spinner.pack_forget()
        self.spinner_label.pack_forget()

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
    def create_supabase_tab(self):
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

    def load_supabase_data(self):
        try:
            self.run_with_spinner(
                task=self.supabase.fetch_template_selection(),
                on_success=self.on_supabase_loaded(),
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
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        for row in data:
            self.tree.insert("", "end", values=list(row.values()))

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


    # ---------------- Upload Tab ----------------
    def create_upload_tab(self):
        tab = self.tabs.tab("Şablon Yükleme")

        # top of the upload tab
        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkButton(
            top_bar,
            text="📂 Görselleri Yükle",
            command=self.upload_images
        ).pack(side="left", padx=(0,10))

        ctk.CTkButton(
            top_bar,
            text="Şablonları Getir",
            command=self.fetch_templates
        ).pack(side="left")

        # content section of the upload tab
        content_frame = ctk.CTkFrame(tab)
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.canvas = tk.Canvas(content_frame, bg="#1f2937", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.preview_frame = tk.Frame(self.canvas, bg="#1f2937")
        self.canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")

        self.preview_frame.bind("<Configure>",lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # scroll with mouse
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # submit, fetch and delete buttons
        bottom_bar = ctk.CTkFrame(tab, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkButton(
            bottom_bar,
            text="Onayla",
            command=self.upload_templates
            ).pack(side="left")

        ctk.CTkButton(
            bottom_bar,
            text="🗑 Seçilenleri Sil",
            fg_color="#B91C1C",
            hover_color="#7F1D1D",
            command=self.delete_selected_templates
        ).pack(side="right")

    # upload template photos to supabase storage
    def upload_images(self):
        paths = filedialog.askopenfilenames(
            title="Şablon Seç",
            filetypes=[("Images", "*.jpg *.png *.webp *.avif")]
        )
        
        self.image_paths.clear()
        self.image_paths.extend(paths)

        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.images.clear()
        self.template_cards = []
        self.templates_ready = False

        self.pil_cache = {}

        try:
            for path in paths:
                # caching - refactor code below
                if path not in self.pil_cache:
                    img = Image.open(path)
                    img.thumbnail((200, 150))
                    photo = ImageTk.PhotoImage(img)
                    self.pil_cache[path] = img
                    self.images.append(photo)

                frame = tk.Frame(self.preview_frame, bg="#111827", width=self.CARD_WIDTH, height=self.CARD_HEIGHT)
                # content on the frame fixed
                frame.grid_propagate(False)

                tk.Label(frame, image=photo, bg="#111827").pack(pady=(6,4))
                tk.Label(
                    frame,
                    text=os.path.basename(path),
                    fg="#9ca3af",
                    bg="#111827",
                    wraplength=self.CARD_WIDTH - 10,
                    justify="center"
                ).pack(padx=5, pady=(0, 6))
        
                self.template_cards.append(frame)

            self.templates_ready = True
            self.relayout_gallery()
            
            self.log(f"Yüklendi: {path}")

        except Exception as e:
            self.log(f"HATA: {e}")

    def upload_templates(self):
        self.run_with_spinner(
            task=lambda:self.supabase.upload_templates_todb(self.image_paths),
            loading_text="Veri tabanına yükleniyor..."
        )

        # clean the screen for futher uploads
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self.images.clear()
    
    # fetch photo list from db
    def fetch_templates(self):
        self._current_cols = None
        threading.Thread(
            target=self.fetch_templates_worker,
            daemon=True
        ).start()

    def fetch_templates_worker(self):
        self.after(0, self.show_spinner)

        try:
            templates = self.supabase.fetch_templates_fromdb()
            self.after(0, lambda: self.show_templates_as_images(templates))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("HATA:", str(e)))

        finally:
            self.after(0, self.hide_spinner)

    # download and show fetched list
    def show_templates_as_images(self, templates):
        # clean previous photo upload residue
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.template_cards = []
        self.templates_ready = False 
        # prevent previous residue before resizing window   
        self._current_cols = None

        self.pil_cache = {}
        self.ctk_cache = {}
    
        try:
            for t in templates:
                filename = t["name"]

                res = self.supabase.download_templates_fromdb(filename)

                # caching mechanism for prevent resizing freeze - refactor code below
                if filename not in self.pil_cache:
                    img = Image.open(BytesIO(res))
                    img = self.phop.crop_center_square(img, 200, 150)
                    self.pil_cache[filename] = img

                if filename not in self.ctk_cache:
                    self.ctk_cache[filename] = ctk.CTkImage(
                    light_image=self.pil_cache[filename],
                    dark_image=self.pil_cache[filename],
                    size=(200, 150)
                )
                ctk_img = self.ctk_cache[filename]    

                frame = ctk.CTkFrame(self.preview_frame, width=self.CARD_WIDTH, height=self.CARD_HEIGHT, corner_radius=12)
                frame.grid_propagate(False)

                lbl = ctk.CTkLabel(frame, image=ctk_img, text="")
                lbl.image = ctk_img
                lbl.pack(padx=10, pady=(10, 5))

                # toggle select added for preventing resizing freeze
                frame.bind("<Button-1>", lambda e, f=frame: self.toggle_select(f))
                lbl.bind("<Button-1>", lambda e, f=frame: self.toggle_select(f))

                self.template_cards.append(frame)

            self.templates_ready = True
            self.relayout_gallery()
        
        except Exception as e:
            print(f"HATA: ({filename}):", e)

    def toggle_select(self, frame):
        selected = getattr(frame, "selected", False)
        frame.selected = not selected
        frame.configure(border_color="#3b82f6" if frame.selected else "#111827", border_width=2)

    def relayout_gallery(self):
        canvas_width = self.canvas.winfo_width()
        if canvas_width < self.CARD_WIDTH:
            return

        cols = max(
            self.MIN_COLS,
            canvas_width // (self.CARD_WIDTH + self.CARD_PAD)
        )

        if getattr(self, "_current_cols", None) == cols:
            return

        self._current_cols = cols

        for i, frame in enumerate(self.template_cards):
            row = i // cols
            col = i % cols
            frame.grid(row=row, column=col, padx=15, pady=15, sticky="n")

    # for calling render_gallery() multiple times
    def on_window_resize(self, event):
        if not self.templates_ready:
            return
        
        if event.widget != self:
            return 

        if hasattr(self, "_resize_job"):
            self.after_cancel(self._resize_job)

        self._resize_job = self.after(120, self.relayout_gallery)

    # delete selected templates from supabase storage
    def delete_selected_templates(self):
        selected = [
            filename
            for filename, var in self.template_widgets
            if var.get()
        ]

        if not selected:
            messagebox.showinfo("Bilgi", "Silinecek şablon seçilmedi.")
            return

        threading.Thread(
            target=self.delete_templates_worker,
            args=(selected,),
            daemon=True
        ).start()

    def delete_templates_worker(self, selected):
        self.after(0, self.show_spinner)

        try:
            for filename in selected:
                self.supabase.delete_template_fromdb(filename)

            # !!! cache mekanizması ekle fotolar çok geç geliyor ve ui donuyor !!!
            self.after(0, self.fetch_templates)
            print("DELETE RESPONSE: Deleted!")

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("HATA: ", str(e)))

        finally:
            self.after(0, self.hide_spinner)

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