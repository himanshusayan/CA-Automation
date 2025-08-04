from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from app.config import settings
from app.database import create_tables
from app.core.scheduler import start_background_tasks
from app.routers import companies, emails, reminders

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ensure logs directory exists
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

app = FastAPI(
    title="CA Email Automation System",
    description="Automated email processing system for CA professionals",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(emails.router, prefix="/api/emails", tags=["emails"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["reminders"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    await create_tables()
    await start_background_tasks()
    logging.info("CA Email Automation System started successfully")

@app.get("/")
async def root():
    return {
        "message": "CA Email Automation System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/categories")
async def get_categories():
    """Get available email categories"""
    return {
        "primary_categories": [
            "GST", "TDS", "INCOME_TAX", "ADVANCE_TAX", 
            "AUDIT", "ROC", "CERTIFICATION", "REFUND", "NOTICE"
        ],
        "gst_sub_categories": [
            "GSTR1", "GSTR3B", "GST_PAYMENT", "GST_REFUND", "GST_NOTICE"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
