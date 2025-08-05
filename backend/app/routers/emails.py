from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.perplexity_service import perplexity_service
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, func
from typing import List, Optional

from app.database import get_db
from app.models import Email
from app.schemas.email import EmailRead
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/classify-all")
async def classify_all_unclassified_emails(db: AsyncSession = Depends(get_db)):
    """Use Perplexity AI to classify ALL unclassified emails"""
    try:
        # Get all unclassified emails
        result = await db.execute(
            select(Email).where(Email.ai_classified == False)
        )
        emails = result.scalars().all()
        
        classified_count = 0
        failed_count = 0
        
        for email in emails:
            success = await perplexity_service.classify_email(db, email)
            if success:
                classified_count += 1
            else:
                failed_count += 1
        
        return {
            "message": f"Classification complete",
            "classified": classified_count,
            "failed": failed_count,
            "total": len(emails)
        }
        
    except Exception as e:
        logger.error(f"Failed to classify emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify emails")

@router.post("/{email_id}/classify")
async def classify_single_email(email_id: int, db: AsyncSession = Depends(get_db)):
    """Use Perplexity AI to classify a single email"""
    try:
        email = await db.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        success = await perplexity_service.classify_email(db, email)
        
        if success:
            await db.refresh(email)
            return {
                "message": "Email classified successfully",
                "category": email.primary_category,
                "sub_category": email.sub_category
            }
        else:
            raise HTTPException(status_code=500, detail="Classification failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to classify email {email_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify email")

@router.get("/", response_model=List[EmailRead])
async def list_emails(
    company_id: Optional[int] = Query(None),
    primary_category: Optional[str] = Query(None),
    data_month: Optional[int] = Query(None),
    data_year: Optional[int] = Query(None),
    is_processed: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return filtered list of emails."""
    try:
        query = select(Email).options(
            selectinload(Email.attachments),
            selectinload(Email.company)
        )

        filters = []
        if company_id:
            filters.append(Email.company_id == company_id)
        if primary_category:
            filters.append(Email.primary_category == primary_category)
        if data_month:
            filters.append(Email.data_month == data_month)
        if data_year:
            filters.append(Email.data_year == data_year)
        if is_processed is not None:
            filters.append(Email.is_processed == is_processed)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(Email.received_date.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    except Exception as e:
        logger.error(f"Failed to list emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve emails")

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
