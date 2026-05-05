import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from database import engine, Base, get_db
from models import DocumentJob
from schemas import DocumentJobResponse, DocumentJobFinalize, DocumentJobUpdate
from tasks import process_document
from redis_client import redis_client

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Async Document Processor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/documents/upload", response_model=List[DocumentJobResponse])
async def upload_documents(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    created_jobs = []
    for file in files:
        job = DocumentJob(
            filename=file.filename,
            file_type=file.content_type or "unknown",
            file_size=file.size or 0,
            status="Queued"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        created_jobs.append(job)
        
        # Trigger Celery task
        process_document.delay(job.id)
        
    return created_jobs

@app.get("/api/documents", response_model=List[DocumentJobResponse])
def list_documents(
    status: Optional[str] = None, 
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db)
):
    query = db.query(DocumentJob)
    
    if status and status != "All":
        query = query.filter(DocumentJob.status == status)
        
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (DocumentJob.filename.ilike(search_term)) | 
            (DocumentJob.id.ilike(search_term))
        )
        
    if sort_order == "desc":
        query = query.order_by(getattr(DocumentJob, sort_by, DocumentJob.created_at).desc())
    else:
        query = query.order_by(getattr(DocumentJob, sort_by, DocumentJob.created_at).asc())
        
    return query.all()

@app.get("/api/documents/{job_id}", response_model=DocumentJobResponse)
def get_document(job_id: str, db: Session = Depends(get_db)):
    job = db.query(DocumentJob).filter(DocumentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.put("/api/documents/{job_id}", response_model=DocumentJobResponse)
def update_document(job_id: str, updates: DocumentJobUpdate, db: Session = Depends(get_db)):
    job = db.query(DocumentJob).filter(DocumentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job, key, value)
        
    db.commit()
    db.refresh(job)
    return job

@app.post("/api/documents/{job_id}/finalize", response_model=DocumentJobResponse)
def finalize_document(job_id: str, data: DocumentJobFinalize, db: Session = Depends(get_db)):
    job = db.query(DocumentJob).filter(DocumentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.final_result = data.final_result
    db.commit()
    db.refresh(job)
    return job

@app.post("/api/documents/{job_id}/retry", response_model=DocumentJobResponse)
def retry_document(job_id: str, db: Session = Depends(get_db)):
    job = db.query(DocumentJob).filter(DocumentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in ["Failed", "Completed"]:
        raise HTTPException(status_code=400, detail="Can only retry Failed or Completed jobs")
        
    job.status = "Queued"
    job.error_message = None
    db.commit()
    db.refresh(job)
    
    # Re-trigger Celery task
    process_document.delay(job.id)
    return job

@app.get("/api/documents/{job_id}/progress")
async def document_progress(job_id: str):
    async def event_generator():
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"job_progress_{job_id}")
        try:
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    yield {
                        "event": "progress",
                        "data": message['data']
                    }
                    data_dict = json.loads(message['data'])
                    if data_dict.get('status') in ['Completed', 'Failed']:
                        break
                await asyncio.sleep(0.5)
        finally:
            pubsub.unsubscribe()
            pubsub.close()

    return EventSourceResponse(event_generator())

@app.get("/api/documents/{job_id}/export")
def export_document(job_id: str, format: str = "json", db: Session = Depends(get_db)):
    job = db.query(DocumentJob).filter(DocumentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if not job.final_result:
        raise HTTPException(status_code=400, detail="Job has no final result yet")
        
    if format == "json":
        return Response(content=json.dumps(job.final_result, indent=2), media_type="application/json")
    elif format == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=job.final_result.keys())
        writer.writeheader()
        writer.writerow(job.final_result)
        return Response(content=output.getvalue(), media_type="text/csv")
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use json or csv")
