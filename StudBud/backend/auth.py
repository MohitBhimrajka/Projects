# backend/auth.py

import streamlit as st
import pandas as pd
from pathlib import Path
import datetime
from typing import Optional, Dict, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.users_file = Path(__file__).parent.parent / "data" / "users.csv"
        self.users_df = self._load_users()

    def _load_users(self) -> pd.DataFrame:
        """Load users from CSV file"""
        try:
            if self.users_file.exists():
                return pd.read_csv(self.users_file)
            else:
                # Create default DataFrame with admin and student users
                df = pd.DataFrame({
                    'user_id': ['USR_001', 'USR_002'],
                    'email': ['admin@atlas.edu', 'student@atlas.edu'],
                    'password': ['admin123', 'student123'],
                    'role': ['admin', 'student'],
                    'name': ['Admin User', 'Student User'],
                    'department': ['Administration', 'Computer Science'],
                    'year': ['NA', 'Third Year'],
                    'created_at': [datetime.datetime.now().isoformat()] * 2,
                    'last_login': [datetime.datetime.now().isoformat()] * 2
                })
                df.to_csv(self.users_file, index=False)
                return df
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return pd.DataFrame()

    def _save_users(self) -> None:
        """Save users to CSV file"""
        try:
            self.users_df.to_csv(self.users_file, index=False)
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user with plaintext password comparison"""
        try:
            # Find user
            user = self.users_df[self.users_df['email'].str.lower() == email.lower()]
            if user.empty:
                return False, "Invalid email or password", None

            user_data = user.iloc[0].to_dict()

            # Simple password comparison
            if password != user_data['password']:
                return False, "Invalid email or password", None

            # Update last login
            self.users_df.loc[self.users_df['email'] == email, 'last_login'] = \
                datetime.datetime.now().isoformat()
            self._save_users()

            return True, "Login successful", {
                'user_id': user_data['user_id'],
                'name': user_data['name'],
                'role': user_data['role']
            }

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, f"Authentication failed: {str(e)}", None

    def register_user(self, user_data: Dict) -> Tuple[bool, str]:
        """Register a new user with plaintext password"""
        try:
            # Check if email already exists
            if self.users_df['email'].str.lower().eq(user_data['email'].lower()).any():
                return False, "Email already registered"

            # Create user record
            new_user = {
                'user_id': f"USR_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                'email': user_data['email'].lower(),
                'password': user_data['password'],  # Store plaintext password (for testing only)
                'role': 'student',  # New registrations are always students
                'name': user_data['name'],
                'department': user_data.get('department', ''),
                'year': user_data.get('year', ''),
                'created_at': datetime.datetime.now().isoformat(),
                'last_login': ''
            }

            # Add to DataFrame
            self.users_df = pd.concat([self.users_df, pd.DataFrame([new_user])], ignore_index=True)
            self._save_users()

            return True, "Registration successful"

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, f"Registration failed: {str(e)}"

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None

def check_authentication():
    """Check if the user is authenticated."""
    return st.session_state.get('authenticated', False)

def require_admin(func):
    """Decorator to require admin role"""
    def wrapper(*args, **kwargs):
        if not st.session_state.get('authenticated', False):
            st.warning("Please login to access this page.")
            return False
        if st.session_state.get('user_role') != 'admin':
            st.error("You don't have permission to access this page.")
            return False
        return func(*args, **kwargs)
    return wrapper

def login_ui():
    """Render login UI and handle authentication"""
    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        auth_manager = AuthManager()
        success, message, user_info = auth_manager.authenticate_user(email, password)
        if success:
            st.session_state.authenticated = True
            st.session_state.user_id = user_info['user_id']
            st.session_state.user_name = user_info['name']
            st.session_state.user_role = user_info['role']
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error(message)

def logout():
    """Log out the user"""
    for key in ['authenticated', 'user_id', 'user_name', 'user_role']:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Logged out successfully.")
    st.experimental_rerun()
