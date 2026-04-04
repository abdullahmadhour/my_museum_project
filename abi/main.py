import os
from pathlib import Path
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import uuid

app = FastAPI()

# --- إعداد المسارات الديناميكية ---
# نحدد مكان الملف الحالي بدقة
current_file_path = Path(__file__).resolve()

# نبحث عن مجلد المشروع الرئيسي
# إذا كان الملف داخل مجلد api أو abi، نرجع خطوة للخلف لنجد static و templates
if current_file_path.parent.name in ["api", "abi", "backend"]:
    BASE_DIR = current_file_path.parent.parent
else:
    BASE_DIR = current_file_path.parent

# تحديد مسارات المجلدات بناءً على المجلد الرئيسي
templates_dir = BASE_DIR / "templates"
static_dir = BASE_DIR / "static"

# طباعة المسارات في الـ Terminal (مفيد جداً للتأكد عند التشغيل على Vercel)
print(f"--- Path Debugging ---")
print(f"Base Directory: {BASE_DIR}")
print(f"Templates Directory: {templates_dir}")
print(f"Static Directory: {static_dir}")

# التحقق من وجود المجلدات قبل محاولة تشغيلها لمنع الـ RuntimeError
if not static_dir.exists():
    print(f"⚠️ تحذير: مجلد static غير موجود في {static_dir}")
    static_dir.mkdir(parents=True, exist_ok=True)

# تحميل القوالب والملفات الثابتة باستخدام المسارات التي حسبناها
templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# --- البيانات المؤقتة ---
bookings_db = []
artifacts_data = [
    {"name": "قناع توت عنخ آمون", "desc": "أشهر تحفة ذهبية في العالم القديم.", "image": "mask.jpg"},
    {"name": "تمثال أبو الهول", "desc": "رمز القوة والحكمة عند قدماء المصريين.", "image": "sphinx.jpg"},
    {"name": "بردية آني", "desc": "نص جنائزي قديم من كتاب الموتى.", "image": "papyrus.jpg"}
]

# --- المسارات (Routes) ---

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    file_path = static_dir / "favicon.ico"
    if file_path.exists():
        return FileResponse(file_path)
    return None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"artifacts": artifacts_data}
    )


@app.post("/booking", response_class=HTMLResponse) 
async def book_ticket(
    request: Request,
    full_name: str = Form(...),
    ticket_type: str = Form(...),
    ticket_count: int = Form(...)
):
    # أسعار التذاكر
    prices = {"egyptian": 60, "foreign": 200, "student": 30}
    total_price = prices.get(ticket_type, 0) * ticket_count
    
    # توليد رقم تذكرة فريد واختصاره لـ 8 حروف
    ticket_id = str(uuid.uuid4())[:8].upper()

    new_booking = {
        "رقم التذكرة": ticket_id,
        "الاسم": full_name,
        "النوع": ticket_type,
        "العدد": ticket_count,
        "الإجمالي": total_price,
        "الحالة": "مؤكد"
    }
    bookings_db.append(new_booking)

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "name": full_name,
            "ticket_id": ticket_id,
            "total": total_price,
            "count": ticket_count
        }
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "12345":
        return RedirectResponse(url="/admin?auth=1", status_code=303)
    return RedirectResponse(url="/login?error=1", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    # حماية بسيطة للوحة الإدارة
    if request.query_params.get("auth") != "1":
        return RedirectResponse(url="/login", status_code=302)
    
    search_query = request.query_params.get("search", "").strip()
    filtered_bookings = [b for b in bookings_db if search_query in b["الاسم"]] if search_query else bookings_db
    total_revenue = sum(b["الإجمالي"] for b in bookings_db)
    
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "bookings": filtered_bookings,
            "count": len(filtered_bookings),
            "revenue": total_revenue,
            "search_query": search_query
        }
    )

@app.get("/logout")
async def logout():
    return RedirectResponse(url="/", status_code=302)




