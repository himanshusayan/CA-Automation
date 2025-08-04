from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ReminderCreate(BaseModel):
    company_id: int
    reminder_month: date
    max_days_to_send: int = 5

class ReminderUpdate(BaseModel):
    max_days_to_send: Optional[int] = None
    is_active: Optional[bool] = None
    manual_stop: Optional[bool] = None

class ReminderRead(BaseModel):
    id: int
    company_id: int
    reminder_month: date
    expected_by_date: date
    max_days_to_send: int
    days_sent: int
    is_active: bool
    manual_stop: bool
    gst_received: bool
    created_at: datetime
    last_sent: Optional[datetime]

    class Config:
        from_attributes = True

class ReminderStats(BaseModel):
    total_active: int
    total_sent_today: int
    companies_pending: int
    companies_completed: int
