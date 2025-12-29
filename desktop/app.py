import os
import time
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from database import SupabaseDB

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FotoModelApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ---------------- Window ----------------
        self.title("Foto Model Studio")
        self.geometry("1400x800")

        self.supabase = SupabaseDB()
        self.all_data = []
        self.images = []
        self.image_paths = []

        self.create_ui()
        self.create_spinner()

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

        ctk.CTkButton(
            tab,
            text="📂 Görselleri Yükle",
            command=self.upload_images
        ).pack(pady=10)

        canvas = tk.Canvas(tab, bg="#1f2937", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.preview_frame = tk.Frame(canvas, bg="#1f2937")
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")
        self.preview_frame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        ctk.CTkButton(
            tab,
            text="Onayla",
            command=lambda: self.upload_templates()
            ).pack(pady=10)
        
        


    def upload_images(self):
        paths = filedialog.askopenfilenames(
            title="Şablon Seç",
            filetypes=[("Images", "*.jpg *.png *.webp *.avif")]
        )
        
        self.image_paths.clear()
        self.image_paths.extend(paths)
        print(self.image_paths)

        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.images.clear()

        row, col = 0, 0
        for path in paths:
            try:
                img = Image.open(path)
                img.thumbnail((180, 180))
                photo = ImageTk.PhotoImage(img)
                self.images.append(photo)

                frame = tk.Frame(self.preview_frame, bg="#111827", padx=5, pady=5)
                frame.grid(row=row, column=col, padx=8, pady=8)

                tk.Label(frame, image=photo, bg="#111827").pack()
                tk.Label(
                    frame,
                    text=os.path.basename(path),
                    fg="#9ca3af",
                    bg="#111827"
                ).pack()

                col += 1
                if col >= 5:
                    col = 0
                    row += 1

                self.log(f"Yüklendi: {path}")

            except Exception as e:
                self.log(f"HATA: {e}")

    

    def upload_templates(self):
        self.run_with_spinner(
            task=lambda:self.supabase.upload_templates_todb(self.image_paths),
            loading_text="Veri tabanına yükleniyor..."
        )

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