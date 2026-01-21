import threading
from tkinter import messagebox

from database import SupabaseDB

class DeleteOps:    
    def __init__(self, fetch, tab, app):
        self.fetch = fetch
        self.tab   = tab
        self.app   = app

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
            print("DELETE RESPONSE: Deleted!")

        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror("HATA: ", str(e)))

        finally:
            self.app.after(50, self.app.spinner.hide_spinner)