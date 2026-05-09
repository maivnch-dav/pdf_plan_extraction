from pathlib import Path
from io import BytesIO
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pypdf import PdfReader
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User, Document, Person, Task
from schemas import VerifyTaskIn, CompleteTaskIn
from extractor import extract_tasks

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TaskFlow MVP API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173","http://127.0.0.1:5173","https://pdfplanextraction.herokuapp.com"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_or_create_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.email == "demo@taskflow.local").first()
    if user: return user
    user = User(name="Demo User", email="demo@taskflow.local")
    db.add(user); db.commit(); db.refresh(user); return user

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    return "\n".join([(page.extract_text() or "") for page in reader.pages]).strip()

def task_to_dict(t: Task):
    return {"id":t.id,"external_id":t.external_id,"title":t.title,"description":t.description,"due_date":t.due_date,"project":t.project,"source_text":t.source_text,"confidence_score":t.confidence_score,"verified":t.verified,"completed":t.completed}

def save_extraction(db: Session, user: User, file_name: str, raw_text: str, extraction: dict) -> Document:
    document = Document(user_id=user.id, file_name=file_name, raw_text=raw_text)
    db.add(document); db.flush()
    for p in extraction.get("people", []):
        person = Person(document_id=document.id, external_id=p["id"], name=p["name"], role=p.get("role", ""))
        db.add(person); db.flush()
        for task in p.get("tasks", []):
            db.add(Task(document_id=document.id, person_id=person.id, external_id=task["id"], title=task["title"], description=task.get("description",""), due_date=task.get("due_date",""), project=task.get("project",""), source_text=task.get("source_text",""), confidence_score=float(task.get("confidence_score",0))))
    db.commit(); db.refresh(document); return document

@app.get("/health")
def health(): return {"status":"ok","service":"TaskFlow MVP API"}

@app.post("/demo/sample")
def load_sample(db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    raw_text = (Path(__file__).parent / "sample_schedule.txt").read_text()
    doc = save_extraction(db, user, "sample_schedule.txt", raw_text, extract_tasks(raw_text))
    return {"document_id":doc.id,"file_name":doc.file_name,"raw_text_preview":raw_text[:500]}

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"): raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    user = get_or_create_demo_user(db)
    raw_text = extract_text_from_pdf(await file.read())
    if not raw_text: raise HTTPException(status_code=400, detail="No text could be extracted. Use a text-based PDF for this MVP.")
    doc = save_extraction(db, user, file.filename, raw_text, extract_tasks(raw_text))
    return {"document_id":doc.id,"file_name":doc.file_name,"raw_text_preview":raw_text[:500]}

@app.get("/documents/{document_id}/people")
def list_people(document_id: int, db: Session = Depends(get_db)):
    people = db.query(Person).filter(Person.document_id == document_id).all()
    return {"people":[{"id":p.id,"external_id":p.external_id,"name":p.name,"role":p.role,"task_count":db.query(Task).filter(Task.person_id == p.id).count()} for p in people]}

@app.get("/people/{person_id}/tasks")
def list_tasks(person_id: int, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person: raise HTTPException(status_code=404, detail="Person not found")
    tasks = db.query(Task).filter(Task.person_id == person_id).all()
    return {"person":{"id":person.id,"name":person.name,"role":person.role},"tasks":[task_to_dict(t) for t in tasks]}

@app.patch("/tasks/{task_id}/verify")
def verify_task(task_id: int, payload: VerifyTaskIn, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    task.verified = payload.verified; db.commit(); return {"id":task.id,"verified":task.verified}

@app.patch("/tasks/{task_id}/complete")
def complete_task(task_id: int, payload: CompleteTaskIn, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    task.completed = payload.completed; db.commit(); return {"id":task.id,"completed":task.completed}

@app.get("/dashboard/{person_id}")
def dashboard(person_id: int, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person: raise HTTPException(status_code=404, detail="Person not found")
    tasks = db.query(Task).filter(Task.person_id == person_id).all()
    return {"person":{"id":person.id,"name":person.name,"role":person.role},"stats":{"total":len(tasks),"verified":sum(1 for t in tasks if t.verified),"completed":sum(1 for t in tasks if t.completed)},"tasks":[task_to_dict(t) for t in tasks]}

_static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if _static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(str(_static_dir / "index.html"))
