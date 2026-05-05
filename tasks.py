import time
import random
from celery_app import celery
from database import SessionLocal
from models import DocumentJob
from redis_client import publish_event
import json

@celery.task(bind=True)
def process_document(self, job_id: str):
    db = SessionLocal()
    job = db.query(DocumentJob).filter(DocumentJob.id == job_id).first()
    if not job:
        db.close()
        return "Job not found"
    
    try:
        # Mark as processing
        job.status = "Processing"
        db.commit()
        publish_event(job_id, "Processing", "job_started", "Processing job started")
        
        # Simulate parsing
        publish_event(job_id, "Processing", "document_parsing_started", "Parsing document")
        time.sleep(random.uniform(1.0, 3.0))
        publish_event(job_id, "Processing", "document_parsing_completed", "Parsing completed")
        
        # Simulate extraction
        publish_event(job_id, "Processing", "field_extraction_started", "Extracting fields")
        time.sleep(random.uniform(2.0, 4.0))
        
        extracted_title = f"Parsed Title for {job.filename}"
        extracted_category = random.choice(["Invoice", "Resume", "Contract", "Report"])
        extracted_summary = f"This is an automatically generated summary for {job.filename}. It contains important details."
        extracted_keywords = [job.file_type, "automated", "async", "celery"]
        
        job.title = extracted_title
        job.category = extracted_category
        job.summary = extracted_summary
        job.keywords = extracted_keywords
        db.commit()
        
        publish_event(job_id, "Processing", "field_extraction_completed", "Extraction completed")
        
        # Finalize processing
        job.status = "Completed"
        job.final_result = {
            "title": extracted_title,
            "category": extracted_category,
            "summary": extracted_summary,
            "keywords": extracted_keywords
        }
        db.commit()
        
        publish_event(job_id, "Completed", "job_completed", "Job successfully completed")
        
    except Exception as e:
        job.status = "Failed"
        job.error_message = str(e)
        db.commit()
        publish_event(job_id, "Failed", "job_failed", f"Job failed: {str(e)}")
    
    finally:
        db.close()
