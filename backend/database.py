import os
import json
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

URL = ""

class SupabaseDB(object):
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    def create_client(self):
        return create_client(SUPABASE_URL, SUPABASE_KEY)

    # fetch original images from db
    def fetch_templates(self, folder="original"):
        files = []
        response = (
            self.supabase
            .storage
            .from_("foto_model")
            .list(f"templates/{folder}")
        )
        
        response = [
            res for res in response
            if not res["name"].startswith(".")
        ]

        for res in response:
            files.append(res["name"])

        return files
    
    def get_public_url(self, filename:str, folder="original"):
        return self.supabase.storage \
                .from_(f"foto_model/templates/{folder}")\
                .get_public_url(filename)
