from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import uuid
from database import supabase

app = FastAPI()
templates = Jinja2Templates(directory="templates")

PHOTO_TEMPLATES = ["4k_1.jpg", "4k_2.jpg", "4k_3.jpg", "4k_4.jpg", "4k_5.jpg", "4k_6.jpg"]

app.mount("/templates", StaticFiles(directory="templates"), name="static")

@app.post("/create-link")
def create_link():
    link_id = str(uuid.uuid4())

    supabase.table("form_links").insert({
        "id": link_id,
        "is_used": False
    }).execute()

    return {
        "url": f"https://YOUR_DOMAIN/form/{link_id}"
    }

@app.get("/form/{link_id}", response_class=HTMLResponse)
def show_form(request: Request, link_id: str):
    link = supabase.table("form_links") \
        .select("*") \
        .eq("id", link_id) \
        .single() \
        .execute()

    if not link.data or link.data["is_used"]:
        return HTMLResponse("Geçersiz veya kullanılmış link")

    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "templates": PHOTO_TEMPLATES,
            "link_id": link_id
        }
    )