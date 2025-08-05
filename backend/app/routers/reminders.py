from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models import Reminder
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderRead, ReminderStats
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------- CRUD ----------

@router.post("/", response_model=ReminderRead)
async def create_reminder(rem: ReminderCreate, db: AsyncSession = Depends(get_db)):
    obj = Reminder(
        company_id=rem.company_id,
        reminder_month=rem.reminder_month,
        expected_by_date=date(rem.reminder_month.year, rem.reminder_month.month, 7),
        max_days_to_send=rem.max_days_to_send,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get("/", response_model=List[ReminderRead])
async def list_reminders(
    active_only: bool = Query(True), db: AsyncSession = Depends(get_db)
):
    q = select(Reminder)
    if active_only:
        q = q.where(Reminder.is_active.is_(True))
    res = await db.execute(q)
    return res.scalars().all()

@router.put("/{reminder_id}", response_model=ReminderRead)
async def update_reminder(
    reminder_id: int, data: ReminderUpdate, db: AsyncSession = Depends(get_db)
):
    obj: Reminder | None = await db.get(Reminder, reminder_id)
    if not obj:
        raise HTTPException(404, "Reminder not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{reminder_id}", status_code=204)
async def delete_reminder(reminder_id: int, db: AsyncSession = Depends(get_db)):
    obj: Reminder | None = await db.get(Reminder, reminder_id)
    if not obj:
        raise HTTPException(404, "Reminder not found")
    await db.delete(obj)
    await db.commit()
    return None

# ---------- extra helpers used by tests ----------

@router.post("/{reminder_id}/stop")
async def stop(reminder_id: int, db: AsyncSession = Depends(get_db)):
    obj: Reminder | None = await db.get(Reminder, reminder_id)
    if not obj:
        raise HTTPException(404)
    obj.manual_stop = True
    await db.commit()
    return {"message": "stopped"}

@router.post("/{reminder_id}/restart")
async def restart(reminder_id: int, db: AsyncSession = Depends(get_db)):
    obj: Reminder | None = await db.get(Reminder, reminder_id)
    if not obj:
        raise HTTPException(404)
    obj.manual_stop = False
    obj.is_active = True
    await db.commit()
    return {"message": "restarted"}

@router.get("/stats", response_model=ReminderStats)
async def stats(db: AsyncSession = Depends(get_db)):
    total_active = await db.scalar(select(func.count(Reminder.id)).where(Reminder.is_active))
    total_sent_today = 0
    companies_pending = 0
    companies_completed = 0
    return ReminderStats(
        total_active=total_active or 0,
        total_sent_today=total_sent_today,
        companies_pending=companies_pending,
        companies_completed=companies_completed,
    )
