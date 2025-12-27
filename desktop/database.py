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

    def upload_templates(self, photos):
        return None
    
    def fetch_data(self):
        return [
            dict(self.supabase
            .table("responses")
            .select("phone_number, full_name, selected_templates, created_at")
            .order("created_at", desc=True)
            .execute())
        ]