from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class AttachmentRead(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_size: int
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class EmailRead(BaseModel):
    id: int
    message_id: str
    sender: str
    subject: Optional[str]
    primary_category: Optional[str]
    sub_category: Optional[str]
    data_month: Optional[int]
    data_year: Optional[int]
    is_processed: bool
    ai_classified: bool
    received_date: datetime
    attachments: List[AttachmentRead] = []

    class Config:
        from_attributes = True

class EmailFilter(BaseModel):
    company_id: Optional[int] = None
    primary_category: Optional[str] = None
    data_month: Optional[int] = None
    data_year: Optional[int] = None
    is_processed: Optional[bool] = None
    limit: int = 50
    offset: int = 0
