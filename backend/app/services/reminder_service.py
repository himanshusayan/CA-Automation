from datetime import datetime, date, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

from app.database import AsyncSessionLocal
from app.models import Reminder, Company, Email
from app.services.email_sender import email_sender
import logging

logger = logging.getLogger(__name__)

class ReminderService:
    
    async def process_daily_reminders(self):
        """Process all pending reminders for today"""
        try:
            async with AsyncSessionLocal() as db:
                # Get all active reminders that need processing
                pending_reminders = await self._get_pending_reminders(db)
                
                logger.info(f"Processing {len(pending_reminders)} pending reminders")
                
                for reminder in pending_reminders:
                    await self._process_reminder(db, reminder)
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error processing daily reminders: {e}")
    
    async def _get_pending_reminders(self, db: AsyncSession) -> List[Reminder]:
        """Get reminders that need to be processed today"""
        today = date.today()
        
        result = await db.execute(
            select(Reminder)
            .options(selectinload(Reminder.company).selectinload(Company.client_emails))
            .where(
                and_(
                    Reminder.is_active == True,
                    Reminder.manual_stop == False,
                    Reminder.gst_received == False,
                    Reminder.days_sent < Reminder.max_days_to_send,
                    Reminder.expected_by_date <= today  # Past due date
                )
            )
        )
        
        return result.scalars().all()
    
    async def _process_reminder(self, db: AsyncSession, reminder: Reminder):
        """Process individual reminder"""
        try:
            # Check if GST email was received for this month
            if await self._check_gst_received(db, reminder):
                reminder.gst_received = True
                reminder.is_active = False
                logger.info(f"GST received for company {reminder.company.name}, stopping reminder")
                return
            
            # Check if we should send reminder today
            if not await self._should_send_today(reminder):
                return
            
            # Send reminder email
            success = await email_sender.send_gst_reminder(
                reminder.company, 
                reminder.reminder_month
            )
            
            if success:
                reminder.days_sent += 1
                reminder.last_sent = datetime.now()
                
                # Stop if max days reached
                if reminder.days_sent >= reminder.max_days_to_send:
                    reminder.is_active = False
                    logger.info(f"Max reminder days reached for company {reminder.company.name}")
            
        except Exception as e:
            logger.error(f"Error processing reminder {reminder.id}: {e}")
    
    async def _check_gst_received(self, db: AsyncSession, reminder: Reminder) -> bool:
        """Check if GST email was received for the reminder month"""
        result = await db.execute(
            select(Email)
            .where(
                and_(
                    Email.company_id == reminder.company_id,
                    Email.primary_category == "GST",
                    Email.data_month == reminder.reminder_month.month,
                    Email.data_year == reminder.reminder_month.year
                )
            )
        )
        
        gst_emails = result.scalars().all()
        return len(gst_emails) > 0
    
    async def _should_send_today(self, reminder: Reminder) -> bool:
        """Determine if reminder should be sent today"""
        if not reminder.last_sent:
            return True  # Never sent before
        
        last_sent_date = reminder.last_sent.date()
        today = date.today()
        
        # Send every day until max days reached
        return last_sent_date < today
    
    async def create_monthly_reminders(self, target_month: date):
        """Create reminders for all companies for a specific month"""
        try:
            async with AsyncSessionLocal() as db:
                # Get all active companies
                result = await db.execute(
                    select(Company).where(Company.is_active == True)
                )
                companies = result.scalars().all()
                
                for company in companies:
                    # Check if reminder already exists for this month
                    existing = await db.execute(
                        select(Reminder)
                        .where(
                            and_(
                                Reminder.company_id == company.id,
                                Reminder.reminder_month == target_month
                            )
                        )
                    )
                    
                    if not existing.scalars().first():
                        # Create new reminder
                        reminder = Reminder(
                            company_id=company.id,
                            reminder_month=target_month,
                            expected_by_date=self._calculate_expected_date(target_month),
                            max_days_to_send=5,  # Default 5 days
                            days_sent=0,
                            is_active=True,
                            manual_stop=False,
                            gst_received=False
                        )
                        
                        db.add(reminder)
                
                await db.commit()
                logger.info(f"Created monthly reminders for {target_month}")
                
        except Exception as e:
            logger.error(f"Error creating monthly reminders: {e}")
    
    def _calculate_expected_date(self, reminder_month: date) -> date:
        """Calculate expected by date (7th of next month)"""
        year = reminder_month.year
        month = reminder_month.month
        
        if month == 12:
            return date(year + 1, 1, 7)
        else:
            return date(year, month + 1, 7)

# Global reminder service instance
reminder_service = ReminderService()
