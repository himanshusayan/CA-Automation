from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    
    # Reminder period
    reminder_month = Column(Date, nullable=False)  # Which month we're expecting data for
    expected_by_date = Column(Date, nullable=False)  # Expected by 7th of next month
    
    # Reminder settings
    max_days_to_send = Column(Integer, default=5)
    days_sent = Column(Integer, default=0)
    
    # Control flags
    is_active = Column(Boolean, default=True)
    manual_stop = Column(Boolean, default=False)
    gst_received = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_sent = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="reminders")
