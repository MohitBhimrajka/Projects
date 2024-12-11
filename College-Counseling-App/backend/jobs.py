import pandas as pd
from datetime import datetime, timedelta
import os
import re

class JobManager:
    def __init__(self):
        self.jobs_file = 'data/jobs.csv'
        if not os.path.exists('data'):
            os.makedirs('data')
        if os.path.exists(self.jobs_file):
            self.jobs_df = pd.read_csv(self.jobs_file)
        else:
            self.jobs_df = pd.DataFrame(columns=[
                'id', 'title', 'company', 'location', 'salary_range',
                'job_type', 'posted_date', 'description', 'skills', 'status'
            ])
            self.jobs_df.to_csv(self.jobs_file, index=False)
        # Ensure 'id' column is present and unique
        if 'id' not in self.jobs_df.columns:
            self.jobs_df['id'] = self.jobs_df.index

    def get_jobs(self, filters=None):
        df = self.jobs_df.copy()
        # Clean salary_range to extract numeric values
        df['salary_min'] = df['salary_range'].apply(lambda x: float(re.findall(r'\d+', x)[0]))
        df['salary_max'] = df['salary_range'].apply(lambda x: float(re.findall(r'\d+', x)[-1]))
        if filters:
            # Apply search query filter
            search_query = filters.get('search_query', '').lower()
            if search_query:
                df = df[
                    df['title'].str.lower().str.contains(search_query, na=False) |
                    df['company'].str.lower().str.contains(search_query, na=False) |
                    df['skills'].str.lower().str.contains(search_query, na=False)
                ]
            # Apply job type filter
            job_types = filters.get('job_types', [])
            if job_types:
                df = df[df['job_type'].isin(job_types)]
            # Apply location filter
            locations = filters.get('locations', [])
            if locations:
                df = df[df['location'].isin(locations)]
            # Apply salary range filter
            salary_min_filter, salary_max_filter = filters.get('salary_range', (0, 100))
            df = df[(df['salary_min'] >= salary_min_filter) & (df['salary_max'] <= salary_max_filter)]
            # Apply sorting
            sort_by = filters.get('sort_by', 'Most Recent')
            if sort_by == 'Most Recent':
                df = df.sort_values(by='posted_date', ascending=False)
            elif sort_by == 'Salary (High to Low)':
                df['avg_salary'] = (df['salary_min'] + df['salary_max']) / 2
                df = df.sort_values(by='avg_salary', ascending=False)
            elif sort_by == 'Salary (Low to High)':
                df['avg_salary'] = (df['salary_min'] + df['salary_max']) / 2
                df = df.sort_values(by='avg_salary', ascending=True)
        return df

    def get_job_by_id(self, job_id):
        job = self.jobs_df[self.jobs_df['id'] == job_id]
        if not job.empty:
            return job.iloc[0].to_dict()
        return None

def get_job_statistics():
    jobs_file = 'data/jobs.csv'
    if not os.path.exists(jobs_file):
        return {}
    jobs_df = pd.read_csv(jobs_file)
    jobs_df['posted_date'] = pd.to_datetime(jobs_df['posted_date'])
    # Clean salary_range to extract numeric values
    jobs_df['salary_min'] = jobs_df['salary_range'].apply(lambda x: float(re.findall(r'\d+', x)[0]))
    jobs_df['salary_max'] = jobs_df['salary_range'].apply(lambda x: float(re.findall(r'\d+', x)[-1]))
    stats = {
        'active_jobs': len(jobs_df),
        'companies': jobs_df['company'].nunique(),
        'recent_jobs': len(jobs_df[jobs_df['posted_date'] >= (datetime.now() - timedelta(days=7))]),
        'salary_ranges': {
            'avg': ((jobs_df['salary_min'] + jobs_df['salary_max']) / 2).mean()
        }
    }
    return stats
