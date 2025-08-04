from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    sanitized_name = Column(String(255), index=True)  # For folder structure
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_emails = relationship("ClientEmail", back_populates="company", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="company")
    reminders = relationship("Reminder", back_populates="company", cascade="all, delete-orphan")
