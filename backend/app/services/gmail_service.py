import os
import base64
import asyncio
from datetime import datetime
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import Email, Attachment, ClientEmail, Company
from app.services.perplexity_service import PerplexityService
from app.services.storage_service import StorageService
import logging

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    
    def __init__(self):
        self.service = None
        self.creds = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        try:
            # Load existing credentials
            if os.path.exists(settings.GMAIL_TOKEN_PATH):
                self.creds = Credentials.from_authorized_user_file(
                    settings.GMAIL_TOKEN_PATH, SCOPES
                )
            
            # Refresh or get new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(settings.GMAIL_CREDENTIALS_PATH):
                        logger.error("Gmail credentials file not found!")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.GMAIL_CREDENTIALS_PATH, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(settings.GMAIL_TOKEN_PATH, 'w') as token:
                    token.write(self.creds.to_json())
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    async def get_registered_emails(self, db: AsyncSession) -> List[str]:
        """Get all active registered client emails"""
        try:
            result = await db.execute(
                select(ClientEmail)
                .options(selectinload(ClientEmail.company))
                .where(ClientEmail.is_active == True)
            )
            client_emails = result.scalars().all()
            return [email.email for email in client_emails if email.company.is_active]
        except Exception as e:
            logger.error(f"Failed to get registered emails: {e}")
            return []
    
    async def fetch_unread_emails(self, db: AsyncSession) -> int:
        """Fetch unread emails from all registered clients"""
        if not self.service:
            if not await self.authenticate():
                return 0
        
        processed_count = 0
        registered_emails = await self.get_registered_emails(db)
        
        logger.info(f"Checking {len(registered_emails)} registered email addresses")
        
        for email_address in registered_emails:
            try:
                count = await self._fetch_from_email(db, email_address)
                processed_count += count
            except Exception as e:
                logger.error(f"Error fetching emails from {email_address}: {e}")
        
        return processed_count
    
    async def _fetch_from_email(self, db: AsyncSession, email_address: str) -> int:
        """Fetch unread emails from specific email address"""
        try:
            # Search for unread emails from this address
            query = f'from:{email_address} is:unread'
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=settings.MAX_EMAILS_PER_FETCH
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} unread emails from {email_address}")
            
            for msg in messages:
                await self._process_email(db, msg['id'], email_address)
            
            return len(messages)
            
        except Exception as e:
            logger.error(f"Error fetching from {email_address}: {e}")
            return 0
    
    async def _process_email(self, db: AsyncSession, message_id: str, sender_email: str):
        """Process individual email"""
        try:
            # Check if email already exists
            existing = await db.execute(
                select(Email).where(Email.message_id == message_id)
            )
            if existing.scalars().first():
                logger.info(f"Email {message_id} already processed")
                return
            
            # Get email details
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            # Extract email information
            headers = message['payload'].get('headers', [])
            subject = self._get_header_value(headers, 'Subject')
            sender = self._get_header_value(headers, 'From')
            date_header = self._get_header_value(headers, 'Date')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            # Get company from sender email
            company = await self._get_company_from_email(db, sender_email)
            
            # Create email record
            email_record = Email(
                message_id=message_id,
                sender=sender,
                subject=subject,
                body=body,
                company_id=company.id if company else None,
                received_date=datetime.now(),
                is_processed=False
            )
            
            db.add(email_record)
            await db.commit()
            await db.refresh(email_record)
            
            logger.info(f"Email {message_id} saved with ID {email_record.id}")
            
            # Process attachments
            await self._process_attachments(db, message, email_record)
            
            # Classify email with AI
            await PerplexityService.classify_email(db, email_record)
            
            # Mark as processed
            email_record.is_processed = True
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error processing email {message_id}: {e}")
            await db.rollback()
    
    def _get_header_value(self, headers: List[dict], name: str) -> str:
        """Get header value by name"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ""
    
    def _extract_body(self, payload: dict) -> str:
        """Extract email body from payload"""
        body = ""
        
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            data = part['body']['data']
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            break
            else:
                if payload['mimeType'] == 'text/plain' and 'data' in payload.get('body', {}):
                    data = payload['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Failed to extract email body: {e}")
        
        return body
    
    async def _get_company_from_email(self, db: AsyncSession, email_address: str) -> Optional[Company]:
        """Get company associated with email address"""
        try:
            result = await db.execute(
                select(ClientEmail)
                .options(selectinload(ClientEmail.company))
                .where(ClientEmail.email == email_address)
                .where(ClientEmail.is_active == True)
            )
            client_email = result.scalars().first()
            return client_email.company if client_email else None
        except Exception as e:
            logger.error(f"Failed to get company for email {email_address}: {e}")
            return None
    
    async def _process_attachments(self, db: AsyncSession, message: dict, email_record: Email):
        """Process and save email attachments"""
        try:
            payload = message['payload']
            
            if 'parts' in payload:
                for part in payload['parts']:
                    filename = part.get('filename')
                    if filename:
                        await self._save_attachment(db, message, part, email_record)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to process attachments for email {email_record.id}: {e}")
            await db.rollback()
    
    async def _save_attachment(self, db: AsyncSession, message: dict, part: dict, email_record: Email):
        """Save individual attachment"""
        try:
            attachment_id = part['body'].get('attachmentId')
            if not attachment_id:
                return
            
            # Download attachment
            attachment = self.service.users().messages().attachments().get(
                userId='me', 
                messageId=message['id'], 
                id=attachment_id
            ).execute()
            
            file_data = base64.urlsafe_b64decode(attachment['data'])
            filename = part['filename']
            
            # Save using storage service if company and classification available
            file_path = None
            if email_record.company and email_record.primary_category:
                # Use AI-detected data period or current date
                data_month = email_record.data_month or datetime.now().month
                data_year = email_record.data_year or datetime.now().year
                
                file_path = StorageService.save_attachment(
                    company_name=email_record.company.name,
                    data_month=data_month,
                    data_year=data_year,
                    category=email_record.primary_category,
                    original_filename=filename,
                    file_data=file_data,
                    email_id=email_record.id
                )
            else:
                # Save to temporary location
                temp_dir = os.path.join(settings.STORAGE_BASE_PATH, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                file_path = os.path.join(temp_dir, f"email_{email_record.id}_{filename}")
                
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            
            # Save attachment record
            attachment_record = Attachment(
                email_id=email_record.id,
                file_name=filename,
                file_path=file_path,
                file_size=len(file_data),
                content_type=part.get('mimeType', 'application/octet-stream')
            )
            
            db.add(attachment_record)
            logger.info(f"Attachment saved: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save attachment {part.get('filename')}: {e}")

# Global instance
gmail_service = GmailService()
