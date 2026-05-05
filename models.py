import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from database import Base

class DocumentJob(Base):
    __tablename__ = "document_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_type = Column(String)
    file_size = Column(Integer)
    status = Column(String, default="Queued") # Queued, Processing, Completed, Failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Extracted data
    title = Column(String, nullable=True)
    category = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)
    
    # Final structured output
    final_result = Column(JSON, nullable=True)
    
    error_message = Column(String, nullable=True)
