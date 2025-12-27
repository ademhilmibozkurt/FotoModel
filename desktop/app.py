import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from database import SupabaseDB

class FotoModelApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # ---------------- Window ----------------
        self.title("Foto Model Studio")
        self.geometry("1400x800")
        self.configure(bg="#0f172a")

        self.all_data = ""
        self.supabase = SupabaseDB()
        self.images = []

        self.setup_style()
        self.create_ui()

    # ---------------- Style ----------------
    def setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background="#1B3C53", foreground="#E3E3E3")
        style.configure("TButton", padding=10, font=("Segoe UI", 11))
        style.configure("TNotebook", background="#1B3C53")
        style.configure("TNotebook.Tab", padding=[20, 10], font=("Segoe UI", 11), background="#234C6A", foreground="#E3E3E3")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10), background="#234C6A", foreground="#E3E3E3")
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#234C6A", foreground="#E3E3E3")

    # ---------------- UI ----------------
    def create_ui(self):
        self.create_header()
        self.create_tabs()
        self.create_log_tab()

    def create_header(self):
        header = tk.Frame(self, bg="#234C6A", height=70)
        logo   = ImageTk.PhotoImage(file="logo.jpg")
        logo_widget = tk.Label(header, image=logo)
        logo_widget.image = logo
        logo_widget.pack(side="left")
        header.pack(fill="x")

        tk.Label(
            header,
            text="Foto Model Stüdyo",
            bg="#234C6A",
            fg="#E3E3E3",
            font=("Segoe UI", 22, "bold")
        ).pack(pady=15)

    def create_tabs(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_supabase_tab()
        self.create_upload_tab()

    # ---------------- Selection Tab ----------------
    def create_supabase_tab(self):
        tab = tk.Frame(self.tabs, bg="#1B3C53")
        self.tabs.add(tab, text="Seçimler")

            # ---- Search Bar ----
        search_frame = tk.Frame(tab, bg="#0f172a")
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(
            search_frame,
            text="Ara:",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 11)
            ).pack(side="left", padx=5)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_tree)

        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=40
        )
        search_entry.pack(side="left", padx=5)

        ttk.Button(
            search_frame,
            text="🔄 Güncelle",
            command=self.load_supabase_data
        ).pack(side="right")

        self.tree = ttk.Treeview(tab)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def load_supabase_data(self):
        try:
            self.all_data = self.supabase.fetch_data()

            self.refresh_tree(self.all_data)
            self.log("Seçimler Getirildi!: ", time.localtime())

        except Exception as e:
            messagebox.showerror("Veritabanı Hatası!", str(e))
            self.log(f"HATA: {e}")
            
    def refresh_tree(self, data):
        self.tree.delete(*self.tree.get_children())

        if not data:
            return
    
        columns = list(data[0].keys())
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=50)

        for row in data:
            self.tree.insert("", "end", values=list(row.values()))   
    
    def filter_tree(self, *args):
        query = self.search_var.get().lower()

        if not query:
            self.refresh_tree(self.all_data)
            return

        filtered = []

        for row in self.all_data:
            if any(query in str(value).lower() for value in row.values()):
                filtered.append(row)

        self.refresh_tree(filtered)

    # ---------------- Upload Tab ----------------
    def create_upload_tab(self):
        tab = tk.Frame(self.tabs, bg="#1B3C53")
        self.tabs.add(tab, text="Şablon Yükleme")

        fileUploadBtn = ttk.Button(tab, text="📂 Görselleri Yükle", command=self.upload_images)
        fileUploadBtn.pack(pady=10)

        canvas = tk.Canvas(tab, bg="#234C6A")
        canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.preview_frame = tk.Frame(canvas, bg="#456882")
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")
        self.preview_frame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        dbUploadBtn = ttk.Button(tab, text="Onayla", command=self.supabase.upload_templates(self.images))
        dbUploadBtn.pack(pady=10)

    def upload_images(self):
        paths = filedialog.askopenfilenames(
            title="Şablon Seç",
            filetypes=[("Images", "*.jpg *.png *.webp *.avif")]
        )

        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.images.clear()

        # fotoğraflar yan yana gözüküyor ve çerçeveyi aşıyor aşağı indir.
        for path in paths:
            try:
                img = Image.open(path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.images.append(photo)

                frame = tk.Frame(self.preview_frame, bg="#234C6A", padx=5, pady=5)
                frame.pack(side="left", padx=5)

                tk.Label(frame, image=photo).pack()
                tk.Label(frame, text=os.path.basename(path), fg="#456882", bg="#234C6A").pack()

                self.log(f"Yüklendi: {path}")

            except Exception as e:
                self.log(f"HATA: {e}")

    # ---------------- Log Tab ----------------
    def create_log_tab(self):
        tab = tk.Frame(self.tabs, bg="#1B3C53")
        self.tabs.add(tab, text="Log")

        self.log_area = tk.Text(
            tab,
            bg="#234C6A",
            fg="#E3E3E3",
            font=("Consolas", 11)
        )
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, message):
        self.log_area.insert("end", f"{message}\n")
        self.log_area.see("end")


if __name__ == "__main__":
    app = FotoModelApp()
    app.mainloop()