import os
import mimetypes
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseDB(object):
    def __init__(self):
        super().__init__()
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # async veya daha hızlı yükleme metodları dene
    def upload_templates(self, paths):
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

    def fetch_data(self):
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
