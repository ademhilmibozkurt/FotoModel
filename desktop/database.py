import os
import json
import requests
import mimetypes
from dotenv import load_dotenv
from supabase import create_client
from photoOperations import PhotoOperations
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseDB(object):
    def __init__(self):
        super().__init__()
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.phop = PhotoOperations()

    # fetch form selections from db
    def fetch_template_selection(self):
        formatted = []
        response = (
            self.supabase
            .table("responses")
            .select("id, phone_number, full_name, selected_templates, created_at")
            .order("created_at", desc=True)
            .execute()
            .data
            )

        # tarih formatını ayarla !!
        # telefon formatını formda ayarla !!
        for item in response:
            formatted.append({
                "id": item.get("id"),
                "Telefon": item.get("phone_number"),
                "İsim": item.get("full_name"),
                "Tarih": item.get("created_at"),
                "Seçimler": item.get("selected_templates")
            })

        return formatted
    
    def update_completed_status(self, record, is_completed):
        self.supabase.table("responses") \
            .update({
                "is_completed": is_completed,
                "completed_at": datetime.utcnow().isoformat() if is_completed else None
            }) \
            .eq("id", record["id"]) \
            .execute()
        
    # get form link for customer use
    def get_link(self, domain="http://127.0.0.1:8000"):
        res = requests.get(f"{domain}/create-link")
        return f"{domain}/form/{res.json()}"

    # fetch işleminde her sefer ui donuyor
    def fetch_templates_fromdb(self, folder="thumbs"):
        response = (
            self.supabase
            .storage
            .from_("foto_model")
            .list(f"templates/{folder}")
        )
        
        return [
            res for res in response
            if not res["name"].startswith(".")
        ]
    
    def download_templates_fromdb(self, filename, folder="thumbs"):
        response = (
            self.supabase
            .storage
            .from_("foto_model")
            .download(f"templates/{folder}/{filename}")
        )
        if not response:
            raise ValueError("Boş response döndü!")

        try:
            json.loads(response.decode("utf-8"))
            raise ValueError("Image yerine JSON döndü (policy veya path hatası)")
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass  

        return response

    # async veya daha hızlı yükleme metodları dene
    def upload_templates_todb(self, paths):
        try:
            for path in paths:
                file_name = os.path.basename(path)

                mime_type, _ = mimetypes.guess_type(path)
                if mime_type is None:
                    raise Exception(f"Mime type bulunamadı: {path}")
                
                # original
                # !!! original fotoları bozulmadan kırpmanın bir yolunu bul !!!
                original_buf = self.phop.resize_original_image(path)
                self.supabase.storage.from_("foto_model").upload(
                    f"templates/original/{file_name}",
                    original_buf,
                    file_options={"content-type": mime_type}
                )

                # thumbnail
                thumb_buf = self.phop.resize_thumb_image(path, width=200, height=200)
                self.supabase.storage.from_("foto_model").upload(
                    f"templates/thumbs/{file_name}",
                    thumb_buf,
                    file_options={"content-type": mime_type}
                )
                    
            print("UPLOAD RESPONSE: Uploaded!")
        except Exception as e:
            print("UPLOAD ERROR: ", e)

    def delete_template_fromdb(self, filename):
        return self.supabase.storage.from_("foto_model").remove([
            f"templates/original/{filename}",
            f"templates/thumbs/{filename}"
        ])