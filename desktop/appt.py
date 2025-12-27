import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from database import SupabaseDB

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # ---------------- Window ----------------
        self.title("Foto Model")
        self.geometry("1000x800")
        self.configure(bg="#f4f6f8")

        self.supabase = SupabaseDB()

        # ---------------- Styles ----------------
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TButton",
            font=("Segoe UI", 11),
            padding=10
        )

        style.configure(
            "Primary.TButton",
            background="#2563eb",
            foreground="white"
        )

        style.map(
            "Primary.TButton",
            background=[("active", "#1e40af")]
        )

        # ---------------- Layout ----------------
        self.create_header()
        self.create_body()
        self.create_footer()

    # ---------------- UI Sections ----------------
    def create_header(self):
        header = tk.Frame(self, bg="#1f2937", height=80)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="📸 Foto Model Yönetim Paneli",
            bg="#1f2937",
            fg="white",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=20)

    def create_body(self):
        body = tk.Frame(self, bg="#f4f6f8")
        body.pack(fill="both", expand=True, padx=20, pady=20)

        # Log alanı
        self.log = tk.Text(
            body,
            font=("Consolas", 11),
            wrap="word",
            relief="solid",
            borderwidth=1
        )

        scrollbar = ttk.Scrollbar(body, command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)

        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_footer(self):
        footer = tk.Frame(self, bg="#f4f6f8")
        footer.pack(fill="x", padx=20, pady=15)

        upload_btn = ttk.Button(
            footer,
            text="📂 Şablon Yükle",
            style="Primary.TButton",
            command=self.upload_photos
        )

        update_btn = ttk.Button(
            footer,
            text="🔄 Güncelle",
            command=self.fetch_selection
        )

        upload_btn.pack(side="left", padx=10)
        update_btn.pack(side="left", padx=10)

    # ---------------- Logic ----------------
    def upload_photos(self):
        file_path = filedialog.askopenfilename(
            title="Şablon Seç",
            initialdir=r"C:\ProgramFiles\FotoModel\templates",
            filetypes=[("Image Files", "*.jpg *.png *.avif *.svg *.webp")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "rb") as f:
                self.lines = f.read()

            self.log.insert("end", f"✔ Yüklendi: {file_path}\n")

        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def fetch_selection(self):
        try:
            form_responses = self.supabase.fetch_data()
            self.log.delete("1.0", "end")
            self.log.insert("end", str(form_responses))
        except Exception as e:
            messagebox.showerror("Supabase Hatası", str(e))


if __name__ == "__main__":
    app = App()
    app.mainloop()
