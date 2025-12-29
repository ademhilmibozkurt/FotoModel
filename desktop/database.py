import os
import json
import mimetypes
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseDB(object):
    def __init__(self):
        super().__init__()
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    def fetch_templates_fromdb(self):
        response = (
            self.supabase
            .storage
            .from_("foto_model")
            .list("templates")
        )
        
        return [
            res for res in response
            if not res["name"].startswith(".")
        ]
    
    def download_templates_fromdb(self, filename):
        response = (
            self.supabase
            .storage
            .from_("foto_model")
            .download(f"templates/{filename}")
        )
        if not response:
            raise ValueError("Boş response döndü")

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

                with open(path, "rb") as file:
                    response = (
                        self.supabase.storage
                        .from_("foto_model")
                        .upload(f"/templates/{file_name}", file, file_options={"content-type": mime_type})
                    )
                    
            print("UPLOAD RESPONSE: ", response)
        except Exception as e:
            print("UPLOAD ERROR: ", e)

    def fetch_template_selection(self):
        formatted = []
        response = (
            self.supabase
            .table("responses")
            .select("phone_number, full_name, selected_templates, created_at")
            .order("created_at", desc=True)
            .execute()
            .data
            )

        # tarih formatını ayarla !!
        # telefon formatını formda ayarla !!
        for item in response:
            formatted.append({
                "Telefon": item.get("phone_number"),
                "İsim": item.get("full_name"),
                "Tarih": item.get("created_at"),
                "Seçimler": item.get("selected_templates")
            })

        return formatted
