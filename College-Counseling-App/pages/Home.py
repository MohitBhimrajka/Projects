import streamlit as st
from pathlib import Path
import pandas as pd
from datetime import datetime
import os
import json

# Add backend directory to path for imports
from backend.auth import check_authentication
from backend.jobs import JobManager, get_job_statistics
from backend.applications import ApplicationManager

class HomeUI:
    def __init__(self):
        self.job_manager = JobManager()
        self.application_manager = ApplicationManager()
        self.setup_page()

    def setup_page(self):
        """Configure page settings and load custom styling."""
        st.set_page_config(
            page_title="Atlas SkillTech Placements",
            page_icon="🎓",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        self.load_custom_css()
        self.init_session_state()

    def load_custom_css(self):
        """Load custom CSS for enhanced visuals."""
        css_path = Path(__file__).parent.parent / "static" / "styles.css"
        if css_path.exists():
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        else:
            st.error("CSS file not found.")

    def init_session_state(self):
        """Initialize session state variables."""
        if 'filters' not in st.session_state:
            st.session_state['filters'] = {}
        if 'view_mode' not in st.session_state:
            st.session_state['view_mode'] = 'list'
        if 'selected_job' not in st.session_state:
            st.session_state['selected_job'] = None

    def render_dashboard_header(self):
        """Render the dashboard header."""
        st.markdown("""
        <div class="dashboard-header">
            <h1>Welcome to Atlas SkillTech Placements</h1>
            <p>Discover opportunities tailored to your aspirations.</p>
        </div>
        """, unsafe_allow_html=True)

    def render_stats_cards(self):
        """Render placement statistics as cards."""
        try:
            stats = get_job_statistics()
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="stats-card">
                    <h3>Active Jobs</h3>
                    <div class="value">{stats.get('active_jobs', 0)}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="stats-card">
                    <h3>Companies</h3>
                    <div class="value">{stats.get('companies', 0)}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="stats-card">
                    <h3>New This Week</h3>
                    <div class="value">{stats.get('recent_jobs', 0)}</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                avg_salary = stats.get('salary_ranges', {}).get('avg', 0)
                st.markdown(f"""
                <div class="stats-card">
                    <h3>Avg Package</h3>
                    <div class="value">₹{avg_salary:.1f} LPA</div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")

    def render_filter_panel(self):
        """Render advanced filters for job listings."""
        st.sidebar.title("Refine Your Search")

        search_query = st.sidebar.text_input("Search jobs, companies, or skills...")
        job_types = st.sidebar.multiselect("Job Type", ["Full-time", "Internship", "Part-time", "Contract"])
        locations = st.sidebar.multiselect("Location", ["Mumbai", "Bangalore", "Remote", "Delhi", "Hyderabad"])
        salary_range = st.sidebar.slider("Salary Range (LPA)", 0, 50, (0, 50))
        sort_by = st.sidebar.selectbox("Sort By", ["Most Recent", "Salary (High to Low)", "Salary (Low to High)"])

        if st.sidebar.button("Apply Filters"):
            # Update filters in session state
            st.session_state['filters'] = {
                "search_query": search_query,
                "job_types": job_types,
                "locations": locations,
                "salary_range": salary_range,
                "sort_by": sort_by,
            }
            # Trigger a rerun
            st.rerun()

    def render_job_listings(self):
        """Render job cards with applied filters."""
        filters = st.session_state.get('filters', {})
        jobs_df = self.job_manager.get_jobs(filters)

        if jobs_df.empty:
            st.warning("No jobs match your criteria.")
            return

        for _, job in jobs_df.iterrows():
            self.render_job_card(job.to_dict())

    def render_job_card(self, job):
        """Render a single job card with interactive elements."""
        st.markdown(f"""
        <div class="job-card">
            <div class="details">
                <div>
                    <h3>{job['title']}</h3>
                    <p><b>Company:</b> {job['company']}</p>
                    <p><b>Location:</b> {job['location']}</p>
                    <p><b>Salary:</b> ₹{job['salary_range']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Quick Apply", key=f"apply_{job['id']}"):
                # Include user_id in application_data
                application_data = {
                    "job_id": job['id'],
                    "user_id": st.session_state.get('user_id', 'anonymous'),
                    "resume": "resume.pdf",  # Replace with actual resume handling
                }
                self.application_manager.submit_application(application_data)
        with col2:
            if st.button("View Details", key=f"details_{job['id']}"):
                st.session_state['view_mode'] = 'details'
                st.session_state['selected_job'] = job['id']
                st.rerun()


    def render_job_details(self, job_id):
        """Render job details page."""
        job = self.job_manager.get_job_by_id(job_id)
        if job is None:
            st.error("Job not found.")
            return

        st.markdown(f"""
        <div class="job-details">
            <h2>{job['title']} at {job['company']}</h2>
            <p><b>Location:</b> {job['location']}</p>
            <p><b>Job Type:</b> {job['job_type']}</p>
            <p><b>Posted Date:</b> {job['posted_date']}</p>
            <p><b>Salary:</b> ₹{job['salary_range']}</p>
            <hr>
            <h3>Description</h3>
            <p>{job['description']}</p>
            <h3>Skills Required</h3>
            <ul>
        """, unsafe_allow_html=True)

        # Parse the 'skills' field, which may be a string representation of a list
        try:
            # Replace single quotes with double quotes and parse JSON
            skills_list = json.loads(job['skills'].replace("'", '"'))
        except json.JSONDecodeError:
            # If parsing fails, treat the skills as a single string
            skills_list = [job['skills']]

        # Display each skill as a list item
        for skill in skills_list:
            st.markdown(f"<li>{skill}</li>", unsafe_allow_html=True)

        st.markdown("</ul></div>", unsafe_allow_html=True)

        # Implement resume upload
        resume_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx"], key=f"resume_{job_id}")
        if st.button("Submit Application"):
            if resume_file is not None:
                resume_content = resume_file.read()
                application_data = {
                    "job_id": job_id,
                    "user_id": st.session_state.get('user_id', 'anonymous'),
                    "resume": ApplicationDocument(
                        file_name=resume_file.name,
                        file_type=resume_file.type,
                        content=resume_content,
                        uploaded_at=datetime.now()
                    ),
                    # Include cover letter if you have a field for it
                }
                self.application_manager.submit_application(application_data)
            else:
                st.warning("Please upload your resume to apply.")

        if st.button("Back to Listings"):
            st.session_state['view_mode'] = 'list'
            st.rerun()

    def main(self):
        """Main function to render the page."""
        if not check_authentication():
            st.warning("Please login to access this page.")
            return

        self.render_dashboard_header()
        self.render_stats_cards()

        if st.session_state['view_mode'] == 'list':
            self.render_filter_panel()
            st.markdown("### Job Listings")
            self.render_job_listings()
        elif st.session_state['view_mode'] == 'details':
            job_id = st.session_state.get('selected_job')
            self.render_job_details(job_id)

if __name__ == "__main__":
    ui = HomeUI()
    ui.main()
