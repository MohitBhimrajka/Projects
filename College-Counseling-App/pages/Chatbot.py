# pages/Chatbot.py

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import random

# Add backend directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.auth import check_authentication
from backend.chatbot import PlacementChatbot, MessageType, Message

class ChatbotUI:
    def __init__(self):
        self.chatbot = PlacementChatbot()
        self.setup_page()

        # Define avatar paths with checks
        user_avatar_path = Path(__file__).parent.parent / "static" / "user_avatar.png"
        assistant_avatar_path = Path(__file__).parent.parent / "static" / "assistant_avatar.png"

        if user_avatar_path.is_file():
            self.user_avatar = str(user_avatar_path)
        else:
            self.user_avatar = "👤"

        if assistant_avatar_path.is_file():
            self.assistant_avatar = str(assistant_avatar_path)
        else:
            self.assistant_avatar = "🤖"

    def setup_page(self):
        """Configure page settings and styling"""
        st.set_page_config(
            page_title="Atlas SkillTech - AI Assistant",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        self.load_custom_css()

    def load_custom_css(self):
        """Load custom CSS for modern chat interface"""
        css_path = Path(__file__).parent.parent / "static" / "chat_styles.css"
        if css_path.exists():
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        else:
            st.error("CSS file not found.")

    def init_session_state(self):
        """Initialize session state variables"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []

        if 'suggestions' not in st.session_state:
            st.session_state.suggestions = []

        if 'preferences' not in st.session_state:
            st.session_state.preferences = {}

        if 'user_resume_text' not in st.session_state:
            st.session_state.user_resume_text = ""

    def format_time(self, timestamp: datetime) -> str:
        """Format timestamp for messages"""
        return timestamp.strftime("%I:%M %p")

    def render_chat_interface(self):
        """Render the main chat interface using st.chat_* functions"""
        self.init_session_state()

        # Use a container for the chat interface
        with st.container():
            # Display chat messages
            for message in st.session_state.messages:
                if message.sender == 'user':
                    with st.chat_message("user", avatar=self.user_avatar):
                        st.markdown(message.content)
                else:
                    with st.chat_message("assistant", avatar=self.assistant_avatar):
                        st.markdown(message.content)

            # Render suggestions outside the message loop
            if st.session_state.get('suggestions') and st.session_state.get('show_suggestions', True):
                st.markdown("<div class='suggestions'>", unsafe_allow_html=True)
                cols = st.columns(len(st.session_state.suggestions))
                for idx, suggestion in enumerate(st.session_state.suggestions):
                    with cols[idx]:
                        if st.button(f"💡 {suggestion}", key=f"suggestion_{suggestion}"):
                            self.process_user_message(suggestion)
                st.markdown("</div>", unsafe_allow_html=True)
                st.session_state.suggestions = []  # Clear suggestions after rendering

            # Separator line
            st.markdown("<hr>", unsafe_allow_html=True)

            # Input area
            with st.form(key='chat_form', clear_on_submit=True):
                prompt = st.text_input("Type your message here...", key='chat_input')
                uploaded_file = st.file_uploader("Upload a file (optional)", type=['pdf', 'docx', 'png', 'jpg', 'jpeg'])
                submit_button = st.form_submit_button(label='Send')

            if submit_button:
                if (prompt is not None and prompt.strip()) or uploaded_file:
                    self.process_user_message(prompt, uploaded_file)

    def process_user_message(self, prompt: Optional[str], uploaded_file=None):
        """Process user's message and handle uploaded files"""
        # Ensure prompt is a string
        if prompt is None:
            prompt = ''
        user_message_content = prompt
        if uploaded_file:
            user_message_content += f"\n[Uploaded file: {uploaded_file.name}]"
        user_message = Message(user_message_content, MessageType.TEXT, {'role': 'user'}, sender='user')
        st.session_state.messages.append(user_message)
        with st.chat_message("user", avatar=self.user_avatar):
            st.markdown(user_message.content)

        # Read and process uploaded file
        extracted_text = ""
        if uploaded_file:
            extracted_text = self.chatbot.extract_text_from_file(uploaded_file)
            if not extracted_text:
                st.warning("Could not extract text from the uploaded file.")
                return
            else:
                # Store resume text in chatbot instance
                self.chatbot.user_resume_text = extracted_text  # Ensure this line is present
                # Also, set a flag to indicate that a resume has been uploaded
                self.chatbot.resume_uploaded = True

        # Combine prompt and extracted text
        combined_prompt = prompt
        if extracted_text and not prompt.strip():
            combined_prompt = "Please analyze my resume."

        # Set user preferences
        self.chatbot.set_user_preferences(st.session_state.preferences)

        # Display assistant's response with typing animation
        with st.chat_message("assistant", avatar=self.assistant_avatar):
            message_placeholder = st.empty()
            full_response = ""

            # Generate and stream response
            with st.spinner("Generating response..."):
                response_generator = self.chatbot.get_response(combined_prompt)
                for response in response_generator:
                    if response.type != MessageType.SUGGESTION:
                        full_response += response.content
                        message_placeholder.markdown(full_response + "▌")
                    else:
                        st.session_state.suggestions = response.content.split('\n')
            message_placeholder.markdown(full_response)

            # Add assistant's response to session state
            assistant_message = Message(
                full_response,
                response.type,
                {'role': 'assistant'},
                sender='bot'
            )
            st.session_state.messages.append(assistant_message)

    def render_progress_tab(self):
        """Render the progress tab"""
        st.header("📊 Your Progress")
        # Include progress metrics and charts here
        st.metric(
            "Topics Covered",
            len(set(self.chatbot.memory.get_formatted_context(''))),
            "+2 today"
        )
        st.metric(
            "Practice Questions",
            st.session_state.get('questions_answered', 0),
            "+5 today"
        )
        st.metric(
            "Engagement Score",
            f"{random.randint(85, 98)}%",
            "↑ 3%"
        )

    def render_settings_tab(self):
        """Render the settings tab"""
        st.header("⚙️ Settings")
        st.checkbox("Enable suggestions", value=True, key="show_suggestions")
        st.select_slider(
            "Response Length",
            options=["Concise", "Balanced", "Detailed"],
            value="Balanced",
            key="response_length"
        )
        st.text_input("Preferred Industry", key="preferred_industry")
        st.multiselect(
            "Skills of Interest",
            options=["Python", "Machine Learning", "Data Science", "Cloud Computing", "Web Development"],
            key="skills_interest"
        )
        if st.button("Save Preferences"):
            st.session_state.preferences = {
                'industry': st.session_state.get('preferred_industry'),
                'skills': st.session_state.get('skills_interest')
            }
            st.success("Preferences saved!")

        if st.button("🔄 Clear Chat"):
            st.session_state.messages = []
            st.session_state.suggestions = []
            st.session_state.preferences = {}
            st.session_state.user_resume_text = ""
            self.chatbot.user_resume_text = ""
            self.chatbot.resume_uploaded = False
            st.experimental_rerun()

    def main(self):
        """Main chat interface with all components"""
        if not check_authentication():
            st.warning("Please login to access the AI Assistant.")
            return

        # Use tabs to organize content
        tabs = st.tabs(["💬 Chat", "📈 Progress", "⚙️ Settings"])

        with tabs[0]:
            self.render_chat_header()
            self.render_chat_interface()

        with tabs[1]:
            self.render_progress_tab()

        with tabs[2]:
            self.render_settings_tab()

    def render_chat_header(self):
        """Render the main chat interface header"""
        st.markdown("""
        <div class="chat-header">
            <h1>🤖 AI Placement Assistant</h1>
            <p>Your personal guide for placements, career advice, interview preparation, resume analysis, and job matching</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    chatbot_ui = ChatbotUI()
    chatbot_ui.main()