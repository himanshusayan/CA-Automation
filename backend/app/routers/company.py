from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import Company, ClientEmail
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate, CompanyStats
from app.services.storage_service import StorageService
import logging

from backend.app.models.email import Email
from backend.app.models.reminder import Reminder

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=CompanyRead)
async def create_company(company: CompanyCreate, db: AsyncSession = Depends(get_db)):
    """Create a new company with mapped email addresses"""
    try:
        # Check if company already exists
        existing = await db.execute(select(Company).where(Company.name == company.name))
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Company already exists")

        # Create new company
        sanitized_name = StorageService.sanitize_company_name(company.name)
        new_company = Company(
            name=company.name, 
            sanitized_name=sanitized_name
        )
        db.add(new_company)
        await db.flush()

        # Add client emails
        for email_data in company.client_emails:
            # Check if email is already mapped to another company
            existing_email = await db.execute(
                select(ClientEmail).where(ClientEmail.email == email_data.email)
            )
            if existing_email.scalars().first():
                raise HTTPException(
                    status_code=400, 
                    detail=f"Email {email_data.email} is already mapped to another company"
                )
            
            new_email = ClientEmail(email=email_data.email, company_id=new_company.id)
            db.add(new_email)

        await db.commit()
        await db.refresh(new_company)
        
        # Load relationships
        result = await db.execute(
            select(Company)
            .options(selectinload(Company.client_emails))
            .where(Company.id == new_company.id)
        )
        company_with_emails = result.scalars().first()
        
        logger.info(f"Company '{company.name}' created with {len(company.client_emails)} emails")
        return company_with_emails

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create company: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create company")

@router.get("/", response_model=List[CompanyRead])
async def list_companies(
    active_only: bool = Query(True, description="Filter only active companies"),
    db: AsyncSession = Depends(get_db)
):
    """List all companies with their mapped emails"""
    try:
        query = select(Company).options(selectinload(Company.client_emails))
        
        if active_only:
            query = query.where(Company.is_active == True)
        
        result = await db.execute(query)
        companies = result.scalars().all()
        
        return companies

    except Exception as e:
        logger.error(f"Failed to list companies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve companies")

@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific company with details"""
    try:
        result = await db.execute(
            select(Company)
            .options(selectinload(Company.client_emails))
            .where(Company.id == company_id)
        )
        company = result.scalars().first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return company

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve company")

@router.put("/{company_id}", response_model=CompanyRead)
async def update_company(
    company_id: int, 
    company_update: CompanyUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update company and its email mappings"""
    try:
        company = await db.get(Company, company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Update company name if provided
        if company_update.name:
            company.name = company_update.name
            company.sanitized_name = StorageService.sanitize_company_name(company_update.name)

        # Update client emails if provided
        if company_update.client_emails is not None:
            # Remove existing emails
            existing_emails = await db.execute(
                select(ClientEmail).where(ClientEmail.company_id == company_id)
            )
            for email in existing_emails.scalars():
                await db.delete(email)
            
            await db.flush()

            # Add new emails
            for email_data in company_update.client_emails:
                # Check if email is already mapped to another company
                existing_email = await db.execute(
                    select(ClientEmail)
                    .where(ClientEmail.email == email_data.email)
                    .where(ClientEmail.company_id != company_id)
                )
                if existing_email.scalars().first():
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Email {email_data.email} is already mapped to another company"
                    )
                
                new_email = ClientEmail(email=email_data.email, company_id=company_id)
                db.add(new_email)

        await db.commit()
        
        # Return updated company with relationships
        result = await db.execute(
            select(Company)
            .options(selectinload(Company.client_emails))
            .where(Company.id == company_id)
        )
        updated_company = result.scalars().first()
        
        logger.info(f"Company {company_id} updated successfully")
        return updated_company

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update company {company_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update company")

@router.delete("/{company_id}", status_code=204)
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    """Delete company and all associated data"""
    try:
        company = await db.get(Company, company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Soft delete (mark as inactive)
        company.is_active = False
        await db.commit()
        
        logger.info(f"Company {company_id} marked as inactive")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete company {company_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete company")

@router.get("/{company_id}/stats", response_model=CompanyStats)
async def get_company_stats(company_id: int, db: AsyncSession = Depends(get_db)):
    """Get company statistics and storage info"""
    try:
        company = await db.get(Company, company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get email counts
        total_emails_result = await db.execute(
            select(func.count(Email.id)).where(Email.company_id == company_id)
        )
        total_emails = total_emails_result.scalar() or 0
        
        # Get GST emails this month
        current_month = datetime.now().month
        current_year = datetime.now().year
        gst_emails_result = await db.execute(
            select(func.count(Email.id))
            .where(Email.company_id == company_id)
            .where(Email.primary_category == "GST")
            .where(Email.data_month == current_month)
            .where(Email.data_year == current_year)
        )
        gst_emails_this_month = gst_emails_result.scalar() or 0
        
        # Get pending reminders
        pending_reminders_result = await db.execute(
            select(func.count(Reminder.id))
            .where(Reminder.company_id == company_id)
            .where(Reminder.is_active == True)
            .where(Reminder.manual_stop == False)
            .where(Reminder.gst_received == False)
        )
        pending_reminders = pending_reminders_result.scalar() or 0
        
        # Get storage info
        storage_info = StorageService.get_company_storage_info(company.name)
        
        return CompanyStats(
            company_id=company_id,
            company_name=company.name,
            total_emails=total_emails,
            gst_emails_this_month=gst_emails_this_month,
            pending_reminders=pending_reminders,
            storage_info=storage_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve company stats")
