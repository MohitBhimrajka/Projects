import streamlit as st
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json

# Add backend directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.auth import check_authentication
from backend.applications import ApplicationManager
from backend.jobs import JobManager

class ApplicationsUI:
    def __init__(self):
        self.app_manager = ApplicationManager()
        self.job_manager = JobManager()
        self.setup_page()
    
    def setup_page(self):
        """Configure page settings and styling"""
        st.set_page_config(
            page_title="Atlas SkillTech - My Applications",
            page_icon="📋",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        self.load_custom_css()
    
    def load_custom_css(self):
        """Load custom CSS styles"""
        st.markdown("""
        <style>
            /* Main container */
            .main {
                background-color: #f8fafc;
                padding: 1rem;
            }
            
            /* Dashboard header */
            .dashboard-header {
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                padding: 2rem;
                border-radius: 12px;
                color: white;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .dashboard-header h1 {
                font-size: 2rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            
            .dashboard-header p {
                font-size: 1.1rem;
                opacity: 0.9;
            }
            
            /* Application cards */
            .application-card {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                border: 1px solid #e5e7eb;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .application-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            /* Status badges */
            .status-badge {
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.875rem;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 0.25rem;
            }
            
            .status-applied {
                background: #e0f2fe;
                color: #0369a1;
            }
            
            .status-review {
                background: #fef3c7;
                color: #92400e;
            }
            
            .status-shortlisted {
                background: #d1fae5;
                color: #065f46;
            }
            
            .status-rejected {
                background: #fee2e2;
                color: #991b1b;
            }
            
            .status-interview {
                background: #e0e7ff;
                color: #3730a3;
            }
            
            /* Timeline */
            .timeline {
                position: relative;
                padding-left: 2rem;
            }
            
            .timeline-item {
                position: relative;
                padding-bottom: 1.5rem;
                border-left: 2px solid #e5e7eb;
                padding-left: 1.5rem;
            }
            
            .timeline-item::before {
                content: '';
                position: absolute;
                left: -0.5rem;
                width: 1rem;
                height: 1rem;
                border-radius: 50%;
                background: white;
                border: 2px solid #4f46e5;
            }
            
            /* Stats cards */
            .stats-card {
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                margin-bottom: 1rem;
            }
            
            .stats-card h3 {
                color: #1f2937;
                font-size: 1.25rem;
                font-weight: 500;
                margin-bottom: 0.5rem;
            }
            
            .stats-card .value {
                font-size: 2rem;
                font-weight: 600;
                color: #4f46e5;
            }
            
            /* Filters */
            .filter-section {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            
            /* Custom buttons */
            .custom-button {
                background-color: #4f46e5;
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 6px;
                font-weight: 500;
                text-align: center;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            
            .custom-button:hover {
                background-color: #4338ca;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def render_dashboard_header(self):
        """Render the main dashboard header"""
        st.markdown("""
        <div class="dashboard-header">
            <h1>📋 My Applications</h1>
            <p>Track and manage your job applications</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_stats_cards(self, stats: Dict):
        """Render application statistics cards"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>Total Applications</h3>
                <div class="value">{stats['total_applications']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stats-card">
                <h3>In Progress</h3>
                <div class="value">{stats['in_progress']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stats-card">
                <h3>Interviews</h3>
                <div class="value">{stats['interviews']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stats-card">
                <h3>Success Rate</h3>
                <div class="value">{stats['success_rate']}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_filters(self):
        """Render application filters"""
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = st.multiselect(
                "Status",
                ["Applied", "Under Review", "Shortlisted", "Interview", "Rejected"]
            )
            
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=30), datetime.now())
            )
        
        with col2:
            companies = st.multiselect(
                "Companies",
                ["Google", "Microsoft", "Amazon", "Meta", "Apple"]
            )
            
            sort_by = st.selectbox(
                "Sort By",
                ["Application Date", "Company", "Status"]
            )
        
        with col3:
            search = st.text_input("Search Applications", placeholder="Enter keywords...")
            
            show_withdrawn = st.checkbox("Show Withdrawn Applications")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return {
            'status': status,
            'date_range': date_range,
            'companies': companies,
            'sort_by': sort_by,
            'search': search,
            'show_withdrawn': show_withdrawn
        }
    
    def get_status_badge(self, status: str) -> str:
        """Generate HTML for status badge"""
        status_colors = {
            'Applied': 'status-applied',
            'Under Review': 'status-review',
            'Shortlisted': 'status-shortlisted',
            'Interview': 'status-interview',
            'Rejected': 'status-rejected'
        }
        
        status_icons = {
            'Applied': '📤',
            'Under Review': '👀',
            'Shortlisted': '⭐',
            'Interview': '🎯',
            'Rejected': '❌'
        }
        
        return f"""
        <span class="status-badge {status_colors.get(status, '')}">
            {status_icons.get(status, '')} {status}
        </span>
        """
    
    def render_application_card(self, application: Dict):
        """Render individual application card"""
        job = self.job_manager.get_jobs({'job_id': application['job_id']}).iloc[0]
        
        st.markdown(f"""
        <div class="application-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h2 style="font-size: 1.5rem; font-weight: 600; color: #1f2937;">
                        {job['title']}
                    </h2>
                    <div style="color: #4b5563; margin-bottom: 1rem;">
                        {job['company']} • {job['location']}
                    </div>
                </div>
                <div>
                    {self.get_status_badge(application['status'])}
                </div>
            </div>
            
            <div style="display: flex; gap: 2rem; margin-bottom: 1rem;">
                <div>
                    <span style="color: #6b7280;">Applied:</span> 
                    {application['applied_date']}
                </div>
                <div>
                    <span style="color: #6b7280;">Package:</span> 
                    {job['salary_range']}
                </div>
                <div>
                    <span style="color: #6b7280;">Type:</span> 
                    {job['job_type']}
                </div>
            </div>
            
            <div class="timeline">
                {self.render_application_timeline(application)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("View Details", key=f"view_{application['application_id']}"):
                st.session_state.selected_application = application['application_id']
        
        with col2:
            if application['status'] == 'Interview':
                if st.button("Prepare for Interview", key=f"prep_{application['application_id']}"):
                    self.show_interview_prep(job)
        
        with col3:
            if st.button("Withdraw", key=f"withdraw_{application['application_id']}"):
                self.show_withdrawal_form(application)

    def render_application_timeline(self, application: Dict) -> str:
        """Render application status timeline"""
        status_flow = {
            'Applied': {'date': application['applied_date'], 'icon': '📤'},
            'Under Review': {'date': '2024-03-15', 'icon': '👀'},
            'Interview Scheduled': {'date': '2024-03-20', 'icon': '📅'},
            'Interviewed': {'date': '2024-03-22', 'icon': '🎯'},
            'Offer': {'date': '2024-03-25', 'icon': '🎉'}
        }
        
        timeline_html = ""
        for status, info in status_flow.items():
            if status in application.get('status_history', [application['status']]):
                timeline_html += f"""
                <div class="timeline-item">
                    <div style="font-weight: 500; color: #1f2937;">
                        {info['icon']} {status}
                    </div>
                    <div style="color: #6b7280; font-size: 0.875rem;">
                        {info['date']}
                    </div>
                </div>
                """
        
        return timeline_html
    
    def show_interview_prep(self, job: Dict):
        """Show interview preparation resources"""
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Interview Preparation</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Company-specific prep
        st.markdown("### Company Research")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            * **Company**: {job['company']}
            * **Industry**: Technology
            * **Role**: {job['title']}
            * **Key Requirements**: {', '.join(eval(job['requirements'])[:3])}
            """)
        
        with col2:
            st.markdown("### Interview Process")
            st.markdown("""
            1. Technical Round (1 hour)
            2. System Design (45 mins)
            3. Behavioral Round (45 mins)
            4. HR Discussion (30 mins)
            """)
        
        # Practice resources
        st.markdown("### Practice Resources")
        tabs = st.tabs(["Technical", "System Design", "Behavioral"])
        
        with tabs[0]:
            self.render_technical_prep()
        with tabs[1]:
            self.render_system_design_prep()
        with tabs[2]:
            self.render_behavioral_prep()
    
    def render_technical_prep(self):
        """Render technical interview preparation content"""
        st.markdown("#### Key Topics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            * Data Structures
                * Arrays and Strings
                * Trees and Graphs
                * Dynamic Programming
            * Algorithms
                * Sorting and Searching
                * Graph Algorithms
                * Optimization
            """)
        
        with col2:
            with st.expander("Practice Questions"):
                st.markdown("""
                1. Implement a balanced binary search tree
                2. Find the shortest path in a weighted graph
                3. Design an LRU cache
                """)
    
    def render_system_design_prep(self):
        """Render system design preparation content"""
        st.markdown("#### System Design Fundamentals")
        
        topics = [
            "Scalability", "Load Balancing", "Caching",
            "Database Sharding", "Microservices", "API Design"
        ]
        
        cols = st.columns(3)
        for i, topic in enumerate(topics):
            with cols[i % 3]:
                st.button(topic, key=f"topic_{topic}")
        
        with st.expander("Sample System Design Questions"):
            st.markdown("""
            1. Design a URL shortening service
            2. Design Instagram's backend
            3. Design a distributed cache
            """)
    
    def render_behavioral_prep(self):
        """Render behavioral interview preparation content"""
        st.markdown("#### STAR Method Practice")
        
        with st.form("star_practice"):
            situation = st.text_area("Situation")
            task = st.text_area("Task")
            action = st.text_area("Action")
            result = st.text_area("Result")
            
            if st.form_submit_button("Analyze Response"):
                self.analyze_star_response(situation, task, action, result)
    
    def show_withdrawal_form(self, application: Dict):
        """Show application withdrawal form"""
        st.markdown("### Withdraw Application")
        
        with st.form("withdrawal_form"):
            reason = st.selectbox(
                "Reason for Withdrawal",
                [
                    "Accepted another offer",
                    "No longer interested",
                    "Location issues",
                    "Salary expectations",
                    "Other"
                ]
            )
            
            details = st.text_area("Additional Details")
            
            if st.form_submit_button("Confirm Withdrawal"):
                self.app_manager.withdraw_application(
                    application['application_id'],
                    f"{reason}: {details}"
                )
                st.success("Application withdrawn successfully")
                st.rerun()
    
    def render_application_analytics(self):
        """Render application analytics and insights"""
        st.markdown("### Application Analytics")
        
        # Application status distribution
        fig_status = px.pie(
            self.get_application_stats(),
            values='count',
            names='status',
            title='Application Status Distribution',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_status, use_container_width=True)
        
        # Timeline visualization
        fig_timeline = go.Figure()
        applications_df = self.app_manager.get_applications(st.session_state.user_id)
        
        fig_timeline.add_trace(go.Scatter(
            x=pd.to_datetime(applications_df['applied_date']),
            y=applications_df.index,
            mode='markers+lines',
            name='Applications'
        ))
        
        fig_timeline.update_layout(
            title='Application Timeline',
            xaxis_title='Date',
            yaxis_title='Number of Applications',
            showlegend=True
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    def get_application_stats(self) -> pd.DataFrame:
        """Get application statistics for visualization"""
        applications_df = self.app_manager.get_applications(st.session_state.user_id)
        status_counts = applications_df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        return status_counts
    
    def main(self):
        """Main application interface"""
        if not check_authentication():
            st.warning("Please login to access your applications.")
            return
        
        # Render header and stats
        self.render_dashboard_header()
        
        stats = {
            'total_applications': 12,  # Replace with actual stats
            'in_progress': 5,
            'interviews': 3,
            'success_rate': 75
        }
        self.render_stats_cards(stats)
        
        # Main layout
        col1, col2 = st.columns([7, 3])
        
        with col1:
            # Filters
            filters = self.render_filters()
            
            # Applications list
            applications = self.app_manager.get_applications(
                user_id=st.session_state.user_id,
                filters=filters
            )
            
            if applications.empty:
                st.info("No applications found matching your criteria.")
            else:
                for _, application in applications.iterrows():
                    self.render_application_card(application)
        
        with col2:
            # Analytics
            self.render_application_analytics()
        
        # Export options
        with st.expander("Export Applications"):
            export_format = st.selectbox(
                "Select Format",
                ["PDF", "Excel", "CSV"]
            )
            
            if st.button("Export"):
                self.export_applications(export_format)
    
    def export_applications(self, format: str):
        """Export applications in selected format"""
        try:
            applications = self.app_manager.get_applications(st.session_state.user_id)
            
            if format == "CSV":
                csv = applications.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "applications.csv",
                    "text/csv"
                )
            elif format == "Excel":
                # Add Excel export functionality
                pass
            elif format == "PDF":
                # Add PDF export functionality
                pass
            
            st.success(f"Applications exported successfully in {format} format!")
            
        except Exception as e:
            st.error(f"Error exporting applications: {str(e)}")

if __name__ == "__main__":
    app_ui = ApplicationsUI()
    app_ui.main()