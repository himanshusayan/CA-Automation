from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, index=True, nullable=False)
    sender = Column(String(255), index=True, nullable=False)
    subject = Column(String(1000))
    body = Column(Text)
    
    # Company association
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # AI Classification
    primary_category = Column(String(100), nullable=True)
    sub_category = Column(String(100), nullable=True)
    
    # Data period (extracted by AI from email content)
    data_month = Column(Integer, nullable=True)  # 1-12
    data_year = Column(Integer, nullable=True)   # 2024, 2025, etc.
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    ai_classified = Column(Boolean, default=False)
    
    # Timestamps
    received_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="emails")
    attachments = relationship("Attachment", back_populates="email", cascade="all, delete-orphan")
