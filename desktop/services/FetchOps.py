import threading
from tkinter import messagebox

from infra.database import SupabaseDB
from ui.UploadTab.Fetch import Fetch

class FetchOps:
    def __init__(self, tab, app):
        self.tab = tab
        self.app = app

        self.supabase = SupabaseDB()
        self.fetch    = Fetch(tab, app)

    # ---- template fetching ------- fetch photo list from db
    def fetch_templates(self, folder="thumbs"):
        if getattr(self, "templates_loading", False):
            return
        
        self.templates_loading = True
        self.tab.switch_button(self.tab.btnDelete, "normal")
        self.tab.switch_button(self.tab.btnGetTemplates, state="disabled")

        threading.Thread(
            target=self._fetch_templates_worker,
            args=(folder,),
            daemon=True
        ).start()

    def _fetch_templates_worker(self, folder):
        self.app.after(0, self.app.spinner.show_spinner)
        self.tab.switch_button(self.tab.btnSubmit, "disabled")
        try:
            templates = self.supabase.fetch_templates_fromdb(folder)
            filenames = [t["name"] for t in templates]
            self.app.after(0, lambda: self.fetch.show_templates(filenames))
        except Exception as e:
            self.app.after(0, lambda:messagebox.showerror("HATA: ", str(e)))

        finally:
            self.app.after(0, self.app.spinner.hide_spinner)
            self.templates_loading = False