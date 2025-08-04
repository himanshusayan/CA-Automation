from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_
from typing import List, Optional

from app.database import get_db
from app.models import Email, Company, Attachment
from app.schemas.email import EmailRead, EmailFilter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[EmailRead])
async def list_emails(
    company_id: Optional[int] = Query(None, description="Filter by company"),
    primary_category: Optional[str] = Query(None, description="Filter by category"),
    data_month: Optional[int] = Query(None, description="Filter by data month"),
    data_year: Optional[int] = Query(None, description="Filter by data year"),
    is_processed: Optional[bool] = Query(None, description="Filter by processing status"),
    limit: int = Query(50, ge=1, le=100, description="Number of emails to return"),
    offset: int = Query(0, ge=0, description="Number of emails to skip"),
    db: AsyncSession = Depends(get_db)
):
    """List emails with filtering options"""
    try:
        query = select(Email).options(
            selectinload(Email.attachments),
            selectinload(Email.company)
        )
        
        # Apply filters
        conditions = []
        if company_id:
            conditions.append(Email.company_id == company_id)
        if primary_category:
            conditions.append(Email.primary_category == primary_category)
        if data_month:
            conditions.append(Email.data_month == data_month)
        if data_year:
            conditions.append(Email.data_year == data_year)
        if is_processed is not None:
            conditions.append(Email.is_processed == is_processed)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Apply pagination
        query = query.order_by(Email.received_date.desc()).offset(offset).limit(limit)
        
        result = await db.execute(query)
        emails = result.scalars().all()
        
        return emails

    except Exception as e:
        logger.error(f"Failed to list emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve emails")

@router.get("/{email_id}", response_model=EmailRead)
async def get_email(email_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific email with attachments"""
    try:
        result = await db.execute(
            select(Email)
            .options(
                selectinload(Email.attachments),
                selectinload(Email.company)
            )
            .where(Email.id == email_id)
        )
        email = result.scalars().first()
        
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        return email

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email {email_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve email")

@router.get("/categories/summary")
async def get_category_summary(
    company_id: Optional[int] = Query(None, description="Filter by company"),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of emails by category"""
    try:
        query = select(
            Email.primary_category,
            func.count(Email.id).label('count')
        ).group_by(Email.primary_category)
        
        if company_id:
            query = query.where(Email.company_id == company_id)
        
        result = await db.execute(query)
        summary = [{"category": row[0], "count": row[1]} for row in result.all()]
        
        return {"summary": summary}

    except Exception as e:
        logger.error(f"Failed to get category summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve category summary")

@router.post("/{email_id}/reprocess")
async def reprocess_email(email_id: int, db: AsyncSession = Depends(get_db)):
    """Manually trigger reprocessing of an email"""
    try:
        email = await db.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Reset processing flags
        email.is_processed = False
        email.ai_classified = False
        
        await db.commit()
        
        # Note: In a full implementation, you would trigger the classification service here
        logger.info(f"Email {email_id} marked for reprocessing")
        
        return {"message": "Email marked for reprocessing"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess email {email_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reprocess email")
