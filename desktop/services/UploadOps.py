import threading
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed

from infra.database import SupabaseDB
from ui.UploadTab.Upload import Upload
from utils.logger import Log

class UploadOps:
    def __init__(self, tab, app):
        self.tab = tab
        self.app = app

        self.logger = Log.db_log()
        self.upload = Upload(tab, app)
        
        # limit the number of parallel operations
        self.UPLOAD_LIMIT = 3
        self.upload_semaphore = threading.Semaphore(self.UPLOAD_LIMIT)

    def upload_images(self):
        self.upload.upload_images_ui_wspinner()
    
    # upload to db
    def upload_templates_todb(self):
        self.app.after(0, self.app.spinner.show_spinner)
        threading.Thread(
            target=self._upload_worker,
            daemon=True
        ).start()
        self.app.desktop_log("Dosyalar veritabanına yüklendi.")
        self.logger.info("Files uploaded to database.")

        self.tab.switch_button(self.tab.btnSubmit)
        self.tab.switch_button(self.tab.btnGetTemplates, "normal")
        
        self.app.after(0, self.upload._clear_preview)

    def _upload_worker(self): 
        errors = self.upload_templates_parallel(self.upload.image_paths)
        if errors:
            messagebox.showerror(
                "Upload Hataları",
                "\n".join(errors[:5])
            )
        
        self.app.desktop_log(f"Dosyalar yüklenirken hata oluştu: {errors}")
        self.logger.error(f"When files uploading to database errors occure: {errors}")
        self.app.after(0, self.app.spinner.hide_spinner)

    def upload_templates_parallel(self, paths: list):
        if not paths:
            return
        
        errors = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self.upload_pair, path): path
                for path in paths
            }

            for future in as_completed(futures):
                err = future.result()
                if err:
                    errors.append(err)
        
        return errors

    def upload_pair(self, path):
        try:
            with self.upload_semaphore:
                supabase = SupabaseDB()
                supabase.upload_template_todb(path, False)
                supabase.upload_template_todb(path, True)
        except Exception as e:
            return str(e)