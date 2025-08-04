import asyncio
import logging
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.gmail_service import gmail_service
from app.services.reminder_service import reminder_service
from app.database import AsyncSessionLocal
from app.config import settings

logger = logging.getLogger(__name__)

class EmailScheduler:
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def fetch_emails_job(self):
        """Background job to fetch emails every 10 seconds"""
        try:
            async with AsyncSessionLocal() as db:
                count = await gmail_service.fetch_unread_emails(db)
                if count > 0:
                    logger.info(f"Processed {count} new emails")
        except Exception as e:
            logger.error(f"Email fetch job failed: {e}")
    
    async def process_reminders_job(self):
        """Background job to process reminders daily"""
        try:
            await reminder_service.process_daily_reminders()
            logger.info("Daily reminder processing completed")
        except Exception as e:
            logger.error(f"Reminder processing job failed: {e}")
    
    async def create_monthly_reminders_job(self):
        """Job to create reminders for new month (runs on 1st of each month)"""
        try:
            current_date = date.today()
            # Create reminders for current month
            await reminder_service.create_monthly_reminders(current_date)
            logger.info(f"Monthly reminders created for {current_date.strftime('%B %Y')}")
        except Exception as e:
            logger.error(f"Monthly reminder creation job failed: {e}")
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            # Email fetching every 10 seconds
            self.scheduler.add_job(
                self.fetch_emails_job,
                'interval',
                seconds=settings.EMAIL_FETCH_INTERVAL,
                id='fetch_emails',
                replace_existing=True
            )
            
            # Reminder processing every hour during business hours (9 AM - 6 PM)
            self.scheduler.add_job(
                self.process_reminders_job,
                'cron',
                hour='9-18',
                id='process_reminders',
                replace_existing=True
            )
            
            # Create monthly reminders on 1st of each month at 9 AM
            self.scheduler.add_job(
                self.create_monthly_reminders_job,
                'cron',
                day=1,
                hour=9,
                id='create_monthly_reminders',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Email and reminder scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Email and reminder scheduler stopped")

# Global scheduler instance
email_scheduler = EmailScheduler()

async def start_background_tasks():
    """Start all background tasks"""
    email_scheduler.start()
