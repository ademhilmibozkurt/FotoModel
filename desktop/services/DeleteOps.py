import threading
from tkinter import messagebox

from infra.database import SupabaseDB
from utils.logger import Log

class DeleteOps:    
    def __init__(self, fetch, tab, app):
        self.fetch = fetch
        self.tab   = tab
        self.app   = app

        self.logger = Log.db_log()
        self.supabase = SupabaseDB()

    # delete selected templates from supabase storage
    def delete_selected_templates(self):
        selected = [
            frame.filename
            for frame in self.fetch.template_cards
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

        self.tab.switch_button(self.tab.btnDelete, "disabled")

    def delete_templates_worker(self, selected):
        self.app.after(0, self.app.spinner.show_spinner)
        try:
            for filename in selected:
                self.supabase.delete_template_fromdb(filename)

            self.app.after(10, self.fetch.fetch_templates)
            self.app.desktop_log("Seçilen dosyalar silindi!")
            self.logger.info("Selected files deleted!")

        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror("HATA: ", str(e)))
            self.app.desktop_log("Seçilen dosyalar silinirken hata oluştu: ",str(e))
            self.logger.error("When files deleting error occure!")
        finally:
            self.app.after(50, self.app.spinner.hide_spinner)