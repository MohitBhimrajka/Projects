# backend/applications.py

from typing import Dict, Optional
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import json
from enum import Enum
from dataclasses import dataclass
import re
import hashlib
import base64

# Import get_db from your database module
from .database import get_db
from .jobs import JobManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApplicationStatus(Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    SHORTLISTED = "Shortlisted"
    INTERVIEW_SCHEDULED = "Interview Scheduled"
    INTERVIEWED = "Interviewed"
    OFFERED = "Offered"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"

@dataclass
class ApplicationDocument:
    file_name: str
    file_type: str
    content: bytes
    uploaded_at: datetime

    def to_dict(self) -> Dict:
        return {
            'file_name': self.file_name,
            'file_type': self.file_type,
            'content': base64.b64encode(self.content).decode('utf-8'),
            'uploaded_at': self.uploaded_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ApplicationDocument':
        return cls(
            file_name=data['file_name'],
            file_type=data['file_type'],
            content=base64.b64decode(data['content']),
            uploaded_at=datetime.fromisoformat(data['uploaded_at'])
        )

# backend/applications.py

import pandas as pd
from pathlib import Path
import datetime
from typing import Dict, Optional

class ApplicationManager:
    class ApplicationStatus:
        PENDING = 'Pending'
        ACCEPTED = 'Accepted'
        REJECTED = 'Rejected'
        WITHDRAWN = 'Withdrawn'
    
    def __init__(self):
        self.applications_file = Path(__file__).parent.parent / "data" / "applications.csv"
        self.applications_df = self._load_applications()
    
    def _load_applications(self) -> pd.DataFrame:
        """Load applications from CSV file"""
        if self.applications_file.exists():
            return pd.read_csv(self.applications_file)
        else:
            # Create an empty DataFrame with the required columns
            df = pd.DataFrame(columns=[
                'application_id', 'user_id', 'job_id', 'applied_date', 'status'
            ])
            df.to_csv(self.applications_file, index=False)
            return df
    
    def _save_applications(self) -> None:
        """Save applications to CSV file"""
        self.applications_df.to_csv(self.applications_file, index=False)
    
    def create_application(self, application_data: Dict) -> str:
        """Create a new application"""
        application_id = f"APP_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        application_data['application_id'] = application_id
        application_data['applied_date'] = datetime.datetime.now().isoformat()
        self.applications_df = pd.concat([self.applications_df, pd.DataFrame([application_data])], ignore_index=True)
        self._save_applications()
        return application_id
    
    def get_applications(self) -> pd.DataFrame:
        """Get all applications"""
        return self.applications_df
    
    def update_application(self, application_id: str, updates: Dict) -> bool:
        """Update an application"""
        idx = self.applications_df.index[self.applications_df['application_id'] == application_id]
        if not idx.empty:
            for key, value in updates.items():
                self.applications_df.at[idx[0], key] = value
            self._save_applications()
            return True
        else:
            return False
    
    def delete_application(self, application_id: str) -> bool:
        """Delete an application"""
        initial_count = len(self.applications_df)
        self.applications_df = self.applications_df[self.applications_df['application_id'] != application_id]
        self._save_applications()
        return len(self.applications_df) < initial_count

# Export common operations
def submit_application(application_data: Dict) -> str:
    return ApplicationManager().submit_application(application_data)

def create_application(application_data: Dict) -> str:
    return ApplicationManager().create_application(application_data)

def get_applications(
    filters: Optional[Dict] = None,
    user_id: Optional[str] = None,
    sort_by: str = 'applied_date',
    ascending: bool = False
) -> pd.DataFrame:
    return ApplicationManager().get_applications(
        filters=filters,
        user_id=user_id,
        sort_by=sort_by,
        ascending=ascending
    )

def update_application(application_id: str, updates: Dict) -> bool:
    return ApplicationManager().update_application(application_id, updates)

def withdraw_application(application_id: str, reason: Optional[str] = None) -> bool:
    return ApplicationManager().withdraw_application(application_id, reason)

def get_application_statistics(user_id: Optional[str] = None) -> Dict:
    return ApplicationManager().get_application_statistics(user_id)
