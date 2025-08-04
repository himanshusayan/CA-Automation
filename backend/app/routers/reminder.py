from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.models import Reminder, Company
from app.schemas.reminder import ReminderCreate, ReminderRead, ReminderUpdate, ReminderStats
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=ReminderRead)
async def create_reminder(reminder: ReminderCreate, db: AsyncSession = Depends(get_db)):
    """Create a reminder entry for a company and month"""
    try:
        # Calculate expected by date (7th of next month)
        year = reminder.reminder_month.year
        month = reminder.reminder_month.month
        if month == 12:
            expected_year = year + 1
            expected_month = 1
        else:
            expected_year = year
            expected_month = month + 1
        expected_by_date = date(expected_year, expected_month, 7)

        new_reminder = Reminder(
            company_id=reminder.company_id,
            reminder_month=reminder.reminder_month,
            expected_by_date=expected_by_date,
            max_days_to_send=reminder.max_days_to_send,
            days_sent=0,
            is_active=True,
            manual_stop=False,
            gst_received=False
        )

        db.add(new_reminder)
        await db.commit()
        await db.refresh(new_reminder)

        logger.info(f"Created reminder for company_id={reminder.company_id} for month={reminder.reminder_month}")
        return new_reminder

    except Exception as e:
        logger.error(f"Failed to create reminder: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create reminder")

@router.get("/", response_model=List[ReminderRead])
async def list_reminders(
    active_only: bool = Query(True),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List reminders with filtering"""
    try:
        query = select(Reminder).options(selectinload(Reminder.company))
        
        if active_only:
            query = query.where(Reminder.is_active == True)
        if company_id:
            query = query.where(Reminder.company_id == company_id)
            
        result = await db.execute(query)
        reminders = result.scalars().all()
        return reminders
    except Exception as e:
        logger.error(f"Failed to list reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reminders")

@router.put("/{reminder_id}", response_model=ReminderRead)
async def update_reminder(reminder_id: int, reminder_update: ReminderUpdate, db: AsyncSession = Depends(get_db)):
    """Update reminder settings with manual controls"""
    try:
        reminder = await db.get(Reminder, reminder_id)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")

        if reminder_update.max_days_to_send is not None:
            reminder.max_days_to_send = reminder_update.max_days_to_send
        if reminder_update.is_active is not None:
            reminder.is_active = reminder_update.is_active
        if reminder_update.manual_stop is not None:
            reminder.manual_stop = reminder_update.manual_stop

        await db.commit()
        await db.refresh(reminder)

        logger.info(f"Updated reminder {reminder_id}")
        return reminder

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update reminder {reminder_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update reminder")

@router.post("/{reminder_id}/stop")
async def stop_reminder(reminder_id: int, db: AsyncSession = Depends(get_db)):
    """Manually stop a reminder"""
    try:
        reminder = await db.get(Reminder, reminder_id)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")

        reminder.manual_stop = True
        await db.commit()

        logger.info(f"Manually stopped reminder {reminder_id}")
        return {"message": "Reminder stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop reminder {reminder_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to stop reminder")

@router.post("/{reminder_id}/restart")
async def restart_reminder(reminder_id: int, db: AsyncSession = Depends(get_db)):
    """Restart a stopped reminder"""
    try:
        reminder = await db.get(Reminder, reminder_id)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")

        reminder.manual_stop = False
        reminder.is_active = True
        await db.commit()

        logger.info(f"Restarted reminder {reminder_id}")
        return {"message": "Reminder restarted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart reminder {reminder_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to restart reminder")

@router.get("/stats", response_model=ReminderStats)
async def reminder_stats(db: AsyncSession = Depends(get_db)):
    """Get reminder system statistics"""
    try:
        total_active_res = await db.execute(
            select(func.count(Reminder.id)).where(Reminder.is_active == True)
        )
        total_active = total_active_res.scalar() or 0

        today = date.today()
        total_sent_today_res = await db.execute(
            select(func.count(Reminder.id))
            .where(func.date(Reminder.last_sent) == today)
        )
        total_sent_today = total_sent_today_res.scalar() or 0

        companies_pending_res = await db.execute(
            select(func.count(Reminder.id))
            .where(Reminder.is_active == True)
            .where(Reminder.manual_stop == False)
            .where(Reminder.gst_received == False)
        )
        companies_pending = companies_pending_res.scalar() or 0

        companies_completed_res = await db.execute(
            select(func.count(Reminder.id))
            .where(Reminder.gst_received == True)
        )
        companies_completed = companies_completed_res.scalar() or 0

        return ReminderStats(
            total_active=total_active,
            total_sent_today=total_sent_today,
            companies_pending=companies_pending,
            companies_completed=companies_completed
        )
    except Exception as e:
        logger.error(f"Failed to get reminder stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reminder stats")
