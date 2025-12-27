import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseDB(object):
    def __init__(self):
        super().__init__()
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    def upload_templates(self, photos: list):
        print(photos)
        return None
    
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
