from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentJobBase(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None

class DocumentJobCreate(BaseModel):
    filename: str
    file_type: str
    file_size: int

class DocumentJobUpdate(DocumentJobBase):
    pass

class DocumentJobFinalize(BaseModel):
    final_result: Dict[str, Any]

class DocumentJobResponse(DocumentJobBase):
    id: str
    filename: str
    file_type: str
    file_size: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    final_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
