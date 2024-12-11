# pages/Login.py

import streamlit as st
import sys
from pathlib import Path
import time

# Remove st.set_page_config() from here

# Add backend directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.auth import AuthManager, init_session_state

def login_ui():
    # Initialize session state
    init_session_state()

    # Load custom CSS
    st.markdown("""
    <style>
        .login-container {
            max-width: 450px;
            margin: 2rem auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .university-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .university-header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .form-header {
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        .auth-link {
            text-align: center;
            margin-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Main container
    with st.container():
        # Header
        st.markdown("""
            <div class="university-header">
                <h1>Atlas SkillTech University</h1>
                <p>Placement Assistant Portal</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Login/Register container
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Toggle between login and register
        if 'show_register' not in st.session_state:
            st.session_state.show_register = False
        
        if st.session_state.show_register:
            st.markdown('<div class="form-header">Create Account</div>', unsafe_allow_html=True)
            
            with st.form("register_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                department = st.selectbox(
                    "Department",
                    ["Computer Science", "Information Technology", "Electronics", "Mechanical"]
                )
                year = st.selectbox(
                    "Year",
                    ["First Year", "Second Year", "Third Year", "Final Year"]
                )
                
                submitted = st.form_submit_button("Register")
                if submitted:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        auth_manager = AuthManager()
                        success, message = auth_manager.register_user({
                            'name': name,
                            'email': email,
                            'password': password,
                            'department': department,
                            'year': year
                        })
                        if success:
                            st.success(message)
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(message)
            
            if st.button("Back to Login"):
                st.session_state.show_register = False
                st.rerun()
            
        else:
            st.markdown('<div class="form-header">Sign In</div>', unsafe_allow_html=True)
            
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In")
                
                if submitted:
                    auth_manager = AuthManager()
                    success, message, user_data = auth_manager.authenticate_user(email, password)
                    
                    if success:
                        with st.spinner("Logging in..."):
                            st.session_state.authenticated = True
                            st.session_state.user_id = user_data['user_id']
                            st.session_state.user_role = user_data['role']
                            st.session_state.user_name = user_data['name']
                            time.sleep(1)
                            # Redirect based on user role
                            if user_data['role'] == 'admin':
                                st.query_params = {"page": "Admin"}
                                st.session_state.query_params = {"page": "Admin"}
                            else:
                                st.query_params = {"page": "Home"}
                                st.session_state.query_params = {"page": "Home"}
                            st.rerun()
                    else:
                        st.error(message)
            
            if st.button("Create New Account"):
                st.session_state.show_register = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    login_ui()
