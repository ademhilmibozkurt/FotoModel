import os
import json
import requests
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
            raise ValueError("Image yerine JSON döndü (policy veya path hatası)!")
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass  

        return response
    
    # parallel upload
    def upload_template_todb(self, path:str, is_thumb):
        filename = os.path.basename(path)

        # original
        if is_thumb == False:
            original_buf = self.phop.resize_image(path, wC=0.25, hC=0.25)
            self.supabase.storage.from_("foto_model").upload(
                f"templates/original/{filename}",
                original_buf,
                {
                    "content-type": "image/jpeg"
                }
            )
            print("Şu an originalda")

        else:
            # thumbnail
            thumb_buf = self.phop.resize_image(path, wC=0.1, hC=0.1)
            self.supabase.storage.from_("foto_model").upload(
                f"templates/thumbs/{filename}",
                thumb_buf,
                {
                    "content-type": "image/jpeg"
                }
            )
            print("şu an thumbda")

    # ----------- deletion ------------
    def delete_template_fromdb(self, filename):
        try: 
            return self.supabase.storage.from_("foto_model").remove([
                f"templates/original/{filename}",
                f"templates/thumbs/{filename}"
            ])
        except Exception as e:
            print("DELETION ERROR: ", e)