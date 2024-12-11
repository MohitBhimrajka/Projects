import streamlit as st

# Set page configuration at the top
st.set_page_config(
    page_title="Atlas SkillTech University - Placement Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent))

from backend.auth import check_authentication, init_session_state
from backend.database import init_database
from pages.Login import login_ui  # Import the login UI function

def load_css():
    """Load custom CSS"""
    css_file = Path(__file__).parent / "static" / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    # Initialize session state and database
    init_session_state()
    init_database()

    # Load custom CSS
    load_css()

    # Get the current page from query parameters
    query_params = st.query_params
    current_page = query_params.get("page", ["Login"])[0]

    # Check authentication
    if not check_authentication():
        if current_page != "Login":
            # Redirect to login page
            st.query_params = {"page": "Login"}
            st.session_state.query_params = {"page": "Login"}
            st.rerun()
            return
        else:
            login_ui()
            return

    # If authenticated, redirect to appropriate page if on Login page
    if current_page == "Login":
        # Redirect based on user role
        if st.session_state.get('user_role') == 'admin':
            st.query_params = {"page": "Admin"}
            st.session_state.query_params = {"page": "Admin"}
        else:
            st.query_params = {"page": "Home"}
            st.session_state.query_params = {"page": "Home"}
        st.rerun()
        return

    # Display user info in sidebar
    with st.sidebar:
        st.write(f"Welcome, {st.session_state.get('user_name', 'User')}")
        if st.button("Logout", key="logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params = {"page": "Login"}
            st.session_state.query_params = {"page": "Login"}
            st.rerun()
            return

    # Navigation based on user role
    if st.session_state.get('user_role') == 'admin':
        # Show admin page link
        st.sidebar.markdown("[Admin Page](?page=Admin)")
    else:
        # Hide admin page from non-admin users
        pass  # Do nothing

    # Load the appropriate page based on the current_page variable
    if current_page == "Home":
        # Load your Home page module
        from pages.Home import HomeUI
        HomeUI().main()
    elif current_page == "Applications":
        # Load your Applications page module
        from pages.Applications import ApplicationsUI
        ApplicationsUI().main()
    elif current_page == "Admin" and st.session_state.get('user_role') == 'admin':
        # Load your Admin page module
        from pages.Admin import AdminUI
        admin_ui = AdminUI()
        admin_ui.main()
    else:
        st.error("Page not found.")

if __name__ == "__main__":
    main()
