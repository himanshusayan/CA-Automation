import os
import re
from datetime import datetime
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class StorageService:
    
    @staticmethod
    def sanitize_company_name(company_name: str) -> str:
        """Convert company name to folder-safe format"""
        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r'[^\w\s-]', '', company_name.lower())
        sanitized = re.sub(r'[\s-]+', '_', sanitized)
        return sanitized.strip('_')
    
    @staticmethod
    def get_financial_year(month: int, year: int) -> str:
        """Get financial year string (Apr-Mar format)"""
        if month >= 4:  # April onwards
            return f"{year}-{str(year + 1)[2:]}"
        else:  # Jan-Mar
            return f"{year - 1}-{str(year)[2:]}"
    
    @staticmethod
    def get_month_folder(month: int, year: int) -> str:
        """Get month folder name (e.g., 'January-25')"""
        month_names = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return f"{month_names[month]}-{str(year)[2:]}"
    
    @staticmethod
    def create_storage_path(
        company_name: str,
        data_month: int,
        data_year: int,
        category: str,
        filename: str
    ) -> str:
        """Create complete storage path for email attachment"""
        # Sanitize company name
        company_folder = StorageService.sanitize_company_name(company_name)
        
        # Get financial year
        financial_year = StorageService.get_financial_year(data_month, data_year)
        
        # Get month folder
        month_folder = StorageService.get_month_folder(data_month, data_year)
        
        # Build path
        path_parts = [
            settings.STORAGE_BASE_PATH,
            settings.GST_ROOT_FOLDER,
            company_folder,
            financial_year,
            month_folder,
            category
        ]
        
        folder_path = os.path.join(*path_parts)
        file_path = os.path.join(folder_path, filename)
        
        return file_path
    
    @staticmethod
    def ensure_directory_exists(file_path: str) -> None:
        """Create directory structure if it doesn't exist"""
        directory = os.path.dirname(file_path)
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory created/verified: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise
    
    @staticmethod
    def save_attachment(
        company_name: str,
        data_month: int,
        data_year: int,
        category: str,
        original_filename: str,
        file_data: bytes,
        email_id: Optional[int] = None
    ) -> str:
        """Save email attachment to appropriate folder structure"""
        try:
            # Create unique filename with email ID prefix if provided
            if email_id:
                filename = f"email_{email_id}_{original_filename}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{original_filename}"
            
            # Get storage path
            file_path = StorageService.create_storage_path(
                company_name, data_month, data_year, category, filename
            )
            
            # Ensure directory exists
            StorageService.ensure_directory_exists(file_path)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Attachment saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save attachment {original_filename}: {e}")
            raise
