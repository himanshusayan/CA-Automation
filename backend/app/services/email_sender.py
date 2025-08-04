import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import Reminder, Company, ClientEmail
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    
    def __init__(self):
        # Gmail SMTP configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        # You'll need to add email credentials to your .env file
        self.sender_email = "your_ca_email@gmail.com"  # Add to settings
        self.sender_password = "your_app_password"     # Add to settings
    
    async def send_gst_reminder(self, company: Company, reminder_month: date) -> bool:
        """Send GST data reminder email to company"""
        try:
            # Get company email addresses
            if not company.client_emails:
                logger.warning(f"No email addresses found for company {company.name}")
                return False
            
            recipient_emails = [email.email for email in company.client_emails if email.is_active]
            
            if not recipient_emails:
                logger.warning(f"No active email addresses for company {company.name}")
                return False
            
            # Create email content
            subject = f"GST Data Reminder - {reminder_month.strftime('%B %Y')}"
            body = self._create_reminder_email_body(company.name, reminder_month)
            
            # Send email
            success = await self._send_email(recipient_emails, subject, body)
            
            if success:
                logger.info(f"Reminder sent to {company.name} at {', '.join(recipient_emails)}")
            else:
                logger.error(f"Failed to send reminder to {company.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending reminder to {company.name}: {e}")
            return False
    
    def _create_reminder_email_body(self, company_name: str, reminder_month: date) -> str:
        """Create reminder email body content"""
        month_year = reminder_month.strftime('%B %Y')
        
        body = f"""
Dear {company_name},

This is a friendly reminder regarding your GST data submission for {month_year}.

We have not yet received your GST documents for the above-mentioned period. To ensure timely compliance and avoid any penalties, please submit the following documents at your earliest convenience:

• GSTR-1 (Outward Supplies)
• GSTR-3B (Summary Return)
• GST Payment Receipts/Challans
• Any other relevant GST documents

Please send the documents as email attachments or contact us if you have already submitted them through other means (WhatsApp, physical delivery, etc.).

If you have any questions or need assistance, please don't hesitate to reach out.

Best regards,
CA Team
Phone: [Your Phone Number]
Email: [Your Email]

---
This is an automated reminder. If you have already submitted the documents, please ignore this email.
        """
        
        return body.strip()
    
    async def _send_email(self, recipients: List[str], subject: str, body: str) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                text = msg.as_string()
                server.sendmail(self.sender_email, recipients, text)
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending email: {e}")
            return False

# Global email sender instance
email_sender = EmailSender()
