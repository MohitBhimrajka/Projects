import pandas as pd
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.jobs_file = 'data/jobs.csv'
        self.applications_file = 'data/applications.csv'
        if not os.path.exists('data'):
            os.makedirs('data')
        self._load_jobs()
        self._load_applications()

    def _load_jobs(self):
        if os.path.exists(self.jobs_file):
            self.jobs_df = pd.read_csv(self.jobs_file)
        else:
            self.jobs_df = pd.DataFrame(columns=[
                'id', 'title', 'company', 'location', 'salary_range',
                'job_type', 'posted_date', 'description', 'skills', 'status'
            ])
            self.jobs_df.to_csv(self.jobs_file, index=False)

    def _load_applications(self):
        if os.path.exists(self.applications_file):
            self.applications_df = pd.read_csv(self.applications_file)
        else:
            self.applications_df = pd.DataFrame(columns=[
                'application_id', 'job_id', 'user_id', 'resume', 'applied_date'
            ])
            self.applications_df.to_csv(self.applications_file, index=False)

    def submit_application(self, application_data):
        application_data['application_id'] = f"APP_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}"
        application_data['applied_date'] = datetime.now().isoformat()
        # Replace append with pd.concat
        self.applications_df = pd.concat([self.applications_df, pd.DataFrame([application_data])], ignore_index=True)
        self.applications_df.to_csv(self.applications_file, index=False)

    def get_job_by_id(self, job_id):
        job = self.jobs_df[self.jobs_df['id'] == job_id]
        if not job.empty:
            return job.iloc[0].to_dict()
        return None

# Singleton pattern for database manager
_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance

def init_database():
    """Initialize database connection"""
    return get_db()
