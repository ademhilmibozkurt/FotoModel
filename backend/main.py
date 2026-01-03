from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import uuid
from database import SupabaseDB

app = FastAPI(docs_url="/docs")
templates = Jinja2Templates(directory="templates")

# templateleri veri tabanındaki fotoların isimlerinden al
# PHOTO_TEMPLATES = ["4k_1.jpg", "4k_2.jpg", "4k_3.jpg", "4k_4.jpg", "4k_5.jpg", "4k_6.jpg"]

app.mount("/static", StaticFiles(directory="static"), name="static")

supabase = SupabaseDB()
client   = supabase.create_client()

# get method for desktop apps use
@app.get("/create-link")
def create_link():
    link_id = str(uuid.uuid4())

    res = client.table("form_links").insert({
        "id": link_id,
        "is_used": False
    }).execute()

    if not res.data:
        raise Exception("Insert failed")
    
    return {"link_id":{link_id}}

@app.post("/create-link")
def create_link():
    link_id = str(uuid.uuid4())

    res = client.table("form_links").insert({
        "id": link_id,
        "is_used": False
    }).execute()

    if not res.data:
        raise Exception("Insert failed")
    
    return {
        "url": f"http://127.0.0.1:8000/form/{link_id}"
    }

@app.get("/form/{link_id}", response_class=HTMLResponse)
def show_form(request: Request, link_id: str):
    link = client.table("form_links") \
        .select("*") \
        .eq("id", link_id) \
        .single() \
        .execute()
    
    if not link.data or link.data["is_used"]:
        return HTMLResponse("Geçersiz veya kullanılmış link. Lütfen stüdyo ile iletişime geçin!")

    # call db here. fetch templates from db
    filenames = supabase.fetch_templates()

    photo_templates = [
        supabase.get_public_url(filename)
        for filename in filenames
    ]

    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            # selected images should pass in "templates"
            "templates": photo_templates,
            "link_id": link_id
        }
    )

@app.post("/form/{link_id}")
def submit_form(link_id:str, full_name: str = Form(...), phone_number: str = Form(...),selected_templates: list[str] = Form(...)):
    selected_templates = [temp.split('/')[-1] for temp in selected_templates]
    res = client \
        .table("responses") \
        .insert({
            "full_name": full_name,
            "phone_number": phone_number,
            "selected_templates": selected_templates
        }) \
        .execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Kayıt başarısız!")

    client \
        .table("form_links") \
        .update({"is_used": True}) \
        .eq("id", link_id) \
        .execute()

    return {"status": "ok"}