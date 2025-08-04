import httpx
import json
import logging
from typing import Dict, Tuple, Optional
from app.config import settings
from app.models.email import Email
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class PerplexityService:
    
    CATEGORIES = {
        "PRIMARY": [
            "GST", "TDS", "INCOME_TAX", "ADVANCE_TAX", 
            "AUDIT", "ROC", "CERTIFICATION", "REFUND", "NOTICE"
        ],
        "GST_SUB": [
            "GSTR1", "GSTR3B", "GST_PAYMENT", "GST_REFUND", "GST_NOTICE"
        ]
    }
    
    @staticmethod
    async def classify_email(db: AsyncSession, email_record: Email) -> bool:
        """Classify email using Perplexity AI"""
        try:
            # Prepare prompt for classification
            prompt = PerplexityService._create_classification_prompt(
                email_record.subject or "",
                email_record.body or "",
                email_record.sender
            )
            
            # Call Perplexity API
            classification_result = await PerplexityService._call_perplexity_api(prompt)
            
            if classification_result:
                # Parse and update email record
                await PerplexityService._update_email_classification(
                    db, email_record, classification_result
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to classify email {email_record.id}: {e}")
            return False
    
    @staticmethod
    def _create_classification_prompt(subject: str, body: str, sender: str) -> str:
        """Create prompt for Perplexity AI"""
        prompt = f"""
        You are an AI assistant helping a Chartered Accountant (CA) classify emails from clients.

        Analyze this email and provide the following information in JSON format:

        Email Details:
        - Sender: {sender}
        - Subject: {subject}
        - Body: {body[:1000]}...

        Please analyze and return ONLY a JSON response with these fields:

        {{
            "primary_category": "one of: GST, TDS, INCOME_TAX, ADVANCE_TAX, AUDIT, ROC, CERTIFICATION, REFUND, NOTICE, OTHER",
            "sub_category": "if primary_category is GST, then one of: GSTR1, GSTR3B, GST_PAYMENT, GST_REFUND, GST_NOTICE, else null",
            "company_mentioned": "company name if mentioned in subject/body, else null",
            "data_month": "month number (1-12) if data period is mentioned, else null",
            "data_year": "year (YYYY) if data period is mentioned, else null",
            "confidence": "confidence level 0-100"
        }}

        Focus on Indian CA/GST terminology. Look for keywords like:
        - GST: GSTR-1, GSTR-3B, GST return, GST payment, GST refund
        - TDS: TDS return, TDS certificate, 26AS
        - Income Tax: ITR, income tax return, assessment
        - Advance Tax: advance tax payment, installment
        """
        
        return prompt
    
    @staticmethod
    async def _call_perplexity_api(prompt: str) -> Optional[Dict]:
        """Make API call to Perplexity"""
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Try to extract JSON from response
                try:
                    # Look for JSON in the response
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        return json.loads(json_str)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from Perplexity response: {content}")
                
                return None
                
        except Exception as e:
            logger.error(f"Perplexity API call failed: {e}")
            return None
    
    @staticmethod
    async def _update_email_classification(
        db: AsyncSession, 
        email_record: Email, 
        classification: Dict
    ):
        """Update email record with classification results"""
        try:
            # Update classification fields
            email_record.primary_category = classification.get("primary_category")
            email_record.sub_category = classification.get("sub_category")
            email_record.data_month = classification.get("data_month")
            email_record.data_year = classification.get("data_year")
            email_record.ai_classified = True
            
            # Try to find and associate company if mentioned
            company_mentioned = classification.get("company_mentioned")
            if company_mentioned and not email_record.company_id:
                # Here you could implement company matching logic
                # For now, we'll leave it for manual mapping
                pass
            
            await db.commit()
            logger.info(f"Email {email_record.id} classified as {email_record.primary_category}")
            
        except Exception as e:
            logger.error(f"Failed to update email classification: {e}")
            await db.rollback()
            raise
