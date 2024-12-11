# pages/Admin.py

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import ast  # Imported for literal_eval

# Add backend directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.auth import check_authentication, require_admin, AuthManager
from backend.jobs import JobManager
from backend.applications import ApplicationManager

class AdminUI:
    def __init__(self):
        self.auth_manager = AuthManager()
        self.job_manager = JobManager()
        self.app_manager = ApplicationManager()
        self.load_custom_css()

    def load_custom_css(self):
        """Load custom CSS styles"""
        st.markdown("""
        <style>
            /* Your custom CSS styles */
        </style>
        """, unsafe_allow_html=True)

    @require_admin
    def main(self):
        """Main admin interface"""
        st.title("Admin Panel")
        st.write("Welcome to the admin panel. Here you can manage users, jobs, and applications.")

        tabs = st.tabs(["User Management", "Job Management", "Application Management"])

        with tabs[0]:
            self.user_management()

        with tabs[1]:
            self.job_management()

        with tabs[2]:
            self.application_management()

    def user_management(self):
        """User management functionalities"""
        st.header("User Management")

        # Load users
        users_df = self.auth_manager.users_df

        # Display users
        st.subheader("All Users")
        st.dataframe(users_df[['user_id', 'email', 'name', 'role', 'department', 'year', 'last_login']])

        # Add new user
        st.subheader("Add New User")
        with st.form("add_user_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["student", "admin"])
            department = st.text_input("Department")
            year = st.text_input("Year")

            submitted = st.form_submit_button("Add User")
            if submitted:
                user_data = {
                    'name': name,
                    'email': email,
                    'password': password,
                    'role': role,
                    'department': department,
                    'year': year
                }
                success, message = self.auth_manager.register_user(user_data)
                if success:
                    st.success(message)
                    st.experimental_rerun()
                else:
                    st.error(message)

        # Delete user
        st.subheader("Delete User")
        with st.form("delete_user_form"):
            user_emails = users_df['email'].tolist()
            email_to_delete = st.selectbox("Select User to Delete", user_emails)
            delete_user_submitted = st.form_submit_button("Delete User")
            if delete_user_submitted:
                self.auth_manager.users_df = self.auth_manager.users_df[self.auth_manager.users_df['email'] != email_to_delete]
                self.auth_manager._save_users()
                st.success(f"User {email_to_delete} deleted successfully.")
                st.experimental_rerun()

    def job_management(self):
        """Job management functionalities"""
        st.header("Job Management")

        # Load jobs
        jobs_df = self.job_manager.get_jobs()

        # Display jobs
        st.subheader("All Jobs")
        st.dataframe(jobs_df)

        # Add new job
        st.subheader("Post New Job")
        with st.form("add_job_form"):
            title = st.text_input("Job Title")
            company = st.text_input("Company")
            location = st.text_input("Location")
            job_type = st.selectbox("Job Type", ["Full-time", "Part-time", "Internship"])
            salary_range = st.text_input("Salary Range")
            requirements = st.text_area("Requirements (comma-separated)")
            description = st.text_area("Job Description")
            status = st.selectbox("Status", ["Open", "Closed"])

            submitted = st.form_submit_button("Post Job")
            if submitted:
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'job_type': job_type,
                    'salary_range': salary_range,
                    'requirements': requirements,  # Store as comma-separated string
                    'description': description,
                    'status': status
                }
                job_id = self.job_manager.create_job(job_data)
                st.success(f"Job posted successfully with ID: {job_id}")
                st.experimental_rerun()

        # Edit existing job
        st.subheader("Edit Job")
        job_ids = jobs_df['job_id'].tolist()
        job_id_to_edit = st.selectbox("Select Job to Edit", job_ids)
        job_to_edit = jobs_df[jobs_df['job_id'] == job_id_to_edit].iloc[0].to_dict()

        with st.form("edit_job_form"):
            title = st.text_input("Job Title", value=job_to_edit['title'])
            company = st.text_input("Company", value=job_to_edit['company'])
            location = st.text_input("Location", value=job_to_edit['location'])
            job_type = st.selectbox("Job Type", ["Full-time", "Part-time", "Internship"], index=["Full-time", "Part-time", "Internship"].index(job_to_edit['job_type']))
            salary_range = st.text_input("Salary Range", value=job_to_edit['salary_range'])

            # Handle requirements
            requirements_value = job_to_edit.get('requirements', '')
            if pd.isna(requirements_value):
                requirements_value = ''

            # Use ast.literal_eval if the requirements are stored as a list string
            # Otherwise, treat it as a comma-separated string
            try:
                requirements_list = ast.literal_eval(requirements_value)
                if not isinstance(requirements_list, list):
                    raise ValueError
            except (ValueError, SyntaxError):
                requirements_list = requirements_value.split(',')

            requirements = st.text_area("Requirements (comma-separated)", value=','.join(requirements_list))

            description = st.text_area("Job Description", value=job_to_edit['description'])
            status = st.selectbox("Status", ["Open", "Closed"], index=["Open", "Closed"].index(job_to_edit['status']))

            submitted = st.form_submit_button("Update Job")
            if submitted:
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'job_type': job_type,
                    'salary_range': salary_range,
                    'requirements': requirements,  # Store as comma-separated string
                    'description': description,
                    'status': status
                }
                success = self.job_manager.update_job(job_id_to_edit, job_data)
                if success:
                    st.success("Job updated successfully.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update job.")

        # Delete job
        st.subheader("Delete Job")
        with st.form("delete_job_form"):
            job_id_to_delete = st.selectbox("Select Job to Delete", job_ids, key="delete_job_select")
            delete_job_submitted = st.form_submit_button("Delete Job")
            if delete_job_submitted:
                success = self.job_manager.delete_job(job_id_to_delete)
                if success:
                    st.success(f"Job {job_id_to_delete} deleted successfully.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete job.")

    def application_management(self):
        """Application management functionalities"""
        st.header("Application Management")

        # Load applications
        applications_df = self.app_manager.get_applications()

        if applications_df.empty:
            st.info("No applications found.")
            return

        # Display applications
        st.subheader("All Applications")
        st.dataframe(applications_df)

        # Update application status
        st.subheader("Update Application Status")
        with st.form("update_application_status_form"):
            application_ids = applications_df['application_id'].tolist()
            app_id_to_update = st.selectbox("Select Application to Update", application_ids)
            new_status = st.selectbox("New Status", [
                self.app_manager.ApplicationStatus.PENDING,
                self.app_manager.ApplicationStatus.ACCEPTED,
                self.app_manager.ApplicationStatus.REJECTED,
                self.app_manager.ApplicationStatus.WITHDRAWN
            ])
            update_status_submitted = st.form_submit_button("Update Status")
            if update_status_submitted:
                success = self.app_manager.update_application(app_id_to_update, {'status': new_status})
                if success:
                    st.success("Application status updated successfully.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update application status.")

        # Delete application
        st.subheader("Delete Application")
        with st.form("delete_application_form"):
            app_id_to_delete = st.selectbox("Select Application to Delete", application_ids, key="delete_app_select")
            delete_application_submitted = st.form_submit_button("Delete Application")
            if delete_application_submitted:
                success = self.app_manager.delete_application(app_id_to_delete)
                if success:
                    st.success(f"Application {app_id_to_delete} deleted successfully.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete application.")

if __name__ == "__main__":
    admin_ui = AdminUI()
    admin_ui.main()
