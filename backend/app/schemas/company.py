from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class ClientEmailBase(BaseModel):
    email: EmailStr

class ClientEmailCreate(ClientEmailBase):
    pass

class ClientEmailRead(ClientEmailBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    client_emails: List[ClientEmailCreate] = []

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    client_emails: Optional[List[ClientEmailCreate]] = None

class CompanyRead(CompanyBase):
    id: int
    sanitized_name: Optional[str]
    is_active: bool
    client_emails: List[ClientEmailRead] = []
    created_at: datetime

    class Config:
        from_attributes = True

class CompanyStats(BaseModel):
    company_id: int
    company_name: str
    total_emails: int
    gst_emails_this_month: int
    pending_reminders: int
    storage_info: dict
