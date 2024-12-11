import os
from pathlib import Path

def cleanup():
    # List of data files to remove
    data_files = [
        'data/jobs.csv',
        'data/faq.csv',
        'data/users.csv',
        'data/applications.csv',
        'data/companies.json',
        'data/skills.json',
        'data/courses.json',
        'data/interviews.json'
    ]
    
    print("Cleaning up data files...")
    for file_path in data_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

if __name__ == "__main__":
    cleanup()