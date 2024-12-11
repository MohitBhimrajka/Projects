# backend/chatbot.py

import re
import json
from typing import Generator, List, Dict, Optional
from datetime import datetime
import logging
import sys
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import random
import torch

# Add imports for text extraction and embeddings
from PyPDF2 import PdfReader
import docx
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer, util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure that ollama is installed and import Client
try:
    from ollama import Client
except ImportError:
    logger.error("ollama library is not installed. Please install it to proceed.")
    sys.exit(1)

class MessageType(Enum):
    TEXT = "text"
    QUICK_REPLY = "quick_reply"
    SUGGESTION = "suggestion"
    ERROR = "error"
    SYSTEM = "system"
    RICH_CONTENT = "rich_content"
    CODE = "code"
    INTERVIEW = "interview"
    RESOURCE = "resource"
    RESUME_FEEDBACK = "resume_feedback"
    JOB_MATCH = "job_match"

@dataclass
class Message:
    content: str
    type: MessageType
    metadata: Optional[Dict] = None
    timestamp: datetime = datetime.now()
    sender: str = "bot"
    embedding: Optional[torch.Tensor] = None

class ConversationMemory:
    def __init__(self, max_messages: int = 50):
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def add_message(self, message: Message):
        """Add message and compute embedding"""
        message.embedding = self.embedding_model.encode(message.content, convert_to_tensor=True)
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def get_relevant_context(self, query: str, top_k: int = 5) -> str:
        """Retrieve relevant messages based on semantic similarity"""
        if not self.messages:
            return ""
        query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)
        embeddings = torch.stack([m.embedding for m in self.messages if m.embedding is not None])
        scores = util.pytorch_cos_sim(query_embedding, embeddings).squeeze()
        if scores.dim() == 0:
            # Only one message in embeddings
            top_indices = [0]
        else:
            top_results = torch.topk(scores, k=min(top_k, len(self.messages)))
            top_indices = top_results.indices.tolist()
        context = "\n".join([self.messages[idx].content for idx in top_indices])
        return context

    def get_formatted_context(self, query: str) -> str:
        """Get formatted context for the model"""
        relevant_context = self.get_relevant_context(query)
        if relevant_context:
            return f"Relevant conversation context:\n{relevant_context}"
        else:
            return ""

class PlacementData:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.categories = {
            'companies': self._load_json('companies.json'),
            'skills': self._load_json('skills.json'),
            'courses': self._load_json('courses.json'),
            'interviews': self._load_json('interviews.json'),
            'jobs': self._load_json('jobs.json')  # Assuming you have a jobs.json file
        }

    def _load_json(self, filename: str) -> Dict:
        """Load JSON data with error handling"""
        try:
            with open(self.data_dir / filename) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return {}

class PlacementChatbot:
    def __init__(self):
        self.client = Client()
        self.text_model = "gemma2:27b"  # Using Gemma 2 27B for text
        self.vision_model = "llama3.2-vision:latest"  # For vision-related tasks
        self.memory = ConversationMemory()
        self.placement_data = PlacementData()
        self.user_preferences: Dict = {}
        self.is_mock_interview_active = False
        self.mock_interview_questions = []
        self.current_question_index = 0
        self.user_resume_text = ""  # Initialize the resume text
        self.resume_uploaded = False  # Flag to check if resume is uploaded

        # Refined system prompt
        self.system_prompt = """
You are an AI Placement Assistant for Atlas SkillTech University students.

Your goals:
- Provide comprehensive assistance for placement preparation and career guidance.
- Offer technical advice, interview strategies, and career planning support.
- Conduct mock technical interviews, analyze resumes, and assist with job matching.

Guidelines:
- Use clear, professional language.
- Structure responses with headings and bullet points where appropriate.
- Include examples and actionable steps.
- Maintain an encouraging and supportive tone.
- Personalize responses based on user preferences.

Response Format:
- **Introduction**: Brief acknowledgment.
- **Main Content**: Detailed answer with subheadings.
- **Conclusion**: Summarize key points or suggest next steps.

Example Response:
"Hello! I'd be happy to help you with system design concepts.

**Understanding System Design**

System design involves...

**Best Practices**

- Break down the system...

**Next Steps**

Consider studying..."

Remember to stay focused on placements and career development.
"""

    def get_response(self, query: str) -> Generator[Message, None, None]:
        """Generate streaming response with enhanced features"""
        try:
            # Check if mock interview is active
            if self.is_mock_interview_active:
                # Process mock interview response
                return self.process_mock_interview_response(query)
            else:
                # Check for special commands
                if "start mock interview" in query.lower():
                    return self.start_mock_interview()

                if "analyze my resume" in query.lower() or ("analyze" in query.lower() and "resume" in query.lower()):
                    return self.analyze_resume(query)

                if "find jobs" in query.lower() or "job matching" in query.lower():
                    return self.find_jobs()

                # Prepare prompt
                prompt = self.prepare_response_prompt(query)

                # Add user message to memory
                self.memory.add_message(Message(query, MessageType.TEXT, sender="user"))

                # Generate response
                response = self.client.chat(
                    model=self.text_model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": query}
                    ],
                    stream=True,
                    options={
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_ctx": 8192,
                    }
                )

                # Process and yield response
                current_message = ""
                current_type = MessageType.TEXT

                for chunk in response:
                    if content := chunk.get('message', {}).get('content'):
                        current_message += content

                        # Yield processed message
                        yield Message(
                            content=content,
                            type=current_type,
                            metadata=self._get_message_metadata(current_message, current_type)
                        )

                # Add final response to memory
                self.memory.add_message(Message(
                    current_message,
                    current_type,
                    metadata=self._get_message_metadata(current_message, current_type)
                ))

                # Generate follow-up suggestions
                suggestions = self._generate_suggestions(query, current_message)
                if suggestions:
                    yield Message("\n".join(suggestions), MessageType.SUGGESTION)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield Message(
                "I'm sorry, but I encountered an error while processing your request. Please try again.",
                MessageType.ERROR
            )

    def prepare_response_prompt(self, query: str) -> str:
        """Prepare prompt for the text model"""
        # Start with the system prompt
        prompt = self.system_prompt

        # Include user preferences
        if self.user_preferences:
            preferences_text = "\nUser Preferences:"
            for key, value in self.user_preferences.items():
                if value:
                    preferences_text += f"\n- {key.capitalize()}: {value}"
            prompt += preferences_text

        # Include conversation context
        context = self.memory.get_formatted_context(query)
        if context:
            prompt += f"\n\n{context}"

        # Include the user's query
        prompt += f"\n\nUser Query: {query}"

        return prompt

    def _get_message_metadata(self, message: str, msg_type: MessageType) -> Dict:
        """Generate rich metadata for messages"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'type': msg_type.value
        }
        return metadata

    def _generate_suggestions(self, query: str, response: str) -> List[str]:
        """Generate contextual follow-up suggestions"""
        suggestions = []

        # Simple example of generating suggestions based on the response content
        if "system design" in response.lower():
            suggestions.extend([
                "Can you explain the CAP theorem?",
                "What are some best practices for scaling systems?",
                "How does load balancing work in distributed systems?"
            ])

        if "machine learning" in response.lower():
            suggestions.extend([
                "What is overfitting and how can it be prevented?",
                "Can you explain the bias-variance tradeoff?",
                "What are common evaluation metrics for classification models?"
            ])

        # Personalize suggestions based on user preferences
        preferred_skills = self.user_preferences.get('skills')
        if preferred_skills:
            suggestions.extend([
                f"How can I improve my {skill} skills?" for skill in preferred_skills
            ])

        # Add suggestions for mock interviews and resume analysis
        suggestions.append("Can you start a mock technical interview with me?")
        suggestions.append("Can you analyze my resume?")
        suggestions.append("Can you help me with job matching?")

        # Randomize and limit suggestions
        if suggestions:
            suggestions = list(set(suggestions))  # Remove duplicates
            suggestions = random.sample(suggestions, min(len(suggestions), 3))  # Limit to 3 suggestions

        return suggestions

    # Implement methods to extract text from different file types
    def extract_text_from_pdf(self, uploaded_file) -> str:
        """Extract text from uploaded PDF file"""
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_docx(self, uploaded_file) -> str:
        """Extract text from uploaded DOCX file"""
        try:
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""

    def extract_text_from_image(self, uploaded_file) -> str:
        """Extract text from uploaded image file using llama3.2-vision:latest"""
        try:
            image = Image.open(uploaded_file)
            # Convert image to bytes
            image_bytes = uploaded_file.read()
            # Use the vision model to extract text (assuming the model has this capability)
            response = self.client.generate(
                model=self.vision_model,
                prompt="Extract the text from this image.",
                image=image_bytes,
                max_tokens=500
            )
            extracted_text = response.get('text', '')
            return extracted_text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    def extract_text_from_file(self, uploaded_file) -> str:
        """Extract text based on file type"""
        file_type = uploaded_file.type
        if file_type == 'application/pdf':
            return self.extract_text_from_pdf(uploaded_file)
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return self.extract_text_from_docx(uploaded_file)
        elif file_type in ['image/png', 'image/jpeg']:
            return self.extract_text_from_image(uploaded_file)
        else:
            logger.warning("Unsupported file type.")
            return ""

    def set_user_preferences(self, preferences: Dict):
        """Set user preferences"""
        self.user_preferences = preferences

    # Mock Interview Methods
    def start_mock_interview(self) -> Generator[Message, None, None]:
        """Initiate a mock technical interview"""
        self.is_mock_interview_active = True
        self.mock_interview_questions = self.get_mock_interview_questions()
        self.current_question_index = 0

        question = self.mock_interview_questions[self.current_question_index]
        self.current_question_index += 1

        yield Message(
            f"Let's begin the mock technical interview.\n\n**Question 1:** {question}",
            MessageType.INTERVIEW
        )

    def process_mock_interview_response(self, user_answer: str) -> Generator[Message, None, None]:
        """Process user's answer during mock interview"""
        # Evaluate the user's answer
        evaluation = self.evaluate_answer(user_answer)

        # Provide feedback
        yield Message(
            f"**Feedback:** {evaluation}",
            MessageType.INTERVIEW
        )

        # Check if there are more questions
        if self.current_question_index < len(self.mock_interview_questions):
            question = self.mock_interview_questions[self.current_question_index]
            self.current_question_index += 1
            yield Message(
                f"**Question {self.current_question_index}:** {question}",
                MessageType.INTERVIEW
            )
        else:
            self.is_mock_interview_active = False
            yield Message(
                "This concludes the mock interview. Great job! If you'd like to practice more, let me know.",
                MessageType.INTERVIEW
            )

    def get_mock_interview_questions(self) -> List[str]:
        """Retrieve a set of mock interview questions"""
        # For simplicity, using predefined questions
        return [
            "Can you explain the concept of polymorphism in object-oriented programming?",
            "How does a binary search algorithm work?",
            "What are the differences between TCP and UDP protocols?"
        ]

    def evaluate_answer(self, user_answer: str) -> str:
        """Evaluate the user's answer using the text model"""
        prompt = f"Evaluate the following answer for correctness, completeness, and clarity. Provide constructive feedback.\n\nQuestion: {self.mock_interview_questions[self.current_question_index - 1]}\nAnswer: {user_answer}\n\nFeedback:"
        response = self.client.generate(
            model=self.text_model,
            prompt=prompt,
            max_tokens=150
        )
        return response.get('text', 'Unable to provide feedback at this time.')

    # Resume Analysis Methods
    def analyze_resume(self, query: str) -> Generator[Message, None, None]:
        """Analyze the user's resume"""
        if self.resume_uploaded and self.user_resume_text:
            # Optimize by summarizing the resume if it's too long
            resume_text = self.user_resume_text
            max_resume_length = 1000  # Limit the resume text length

            if len(resume_text) > max_resume_length:
                # Summarize the resume
                summary_prompt = f"Summarize the following resume in 1000 characters or less:\n\n{resume_text}\n\nSummary:"
                summary_response = self.client.generate(
                    model=self.text_model,
                    prompt=summary_prompt,
                    max_tokens=200
                )
                resume_text = summary_response.get('text', resume_text[:max_resume_length])

            # Analyze the (possibly summarized) resume
            prompt = f"Analyze the following resume and provide suggestions for improvement:\n\n{resume_text}\n\nSuggestions:"
            response = self.client.generate(
                model=self.text_model,
                prompt=prompt,
                max_tokens=300
            )

            yield Message(
                response.get('text', 'Unable to analyze resume at this time.'),
                MessageType.RESUME_FEEDBACK
            )
        else:
            yield Message(
                "I haven't received your resume yet. Please upload it, and then ask me to analyze it.",
                MessageType.ERROR
            )

    # Job Matching Methods
    def find_jobs(self) -> Generator[Message, None, None]:
        """Find job opportunities based on user preferences"""
        # For simplicity, we will match jobs based on user's skills
        user_skills = self.user_preferences.get('skills', [])
        matched_jobs = []
        for job in self.placement_data.categories.get('jobs', []):
            if any(skill.lower() in [s.lower() for s in job['required_skills']] for skill in user_skills):
                matched_jobs.append(job)

        if matched_jobs:
            response = "**Here are some job opportunities that match your skills:**\n"
            for job in matched_jobs:
                response += f"- **{job['title']}** at **{job['company']}**\n  Skills Required: {', '.join(job['required_skills'])}\n  Location: {job['location']}\n\n"
            yield Message(
                response,
                MessageType.JOB_MATCH
            )
        else:
            yield Message(
                "Sorry, I couldn't find any job opportunities that match your skills at the moment.",
                MessageType.JOB_MATCH
            )