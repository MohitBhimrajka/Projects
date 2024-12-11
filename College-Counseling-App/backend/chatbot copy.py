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

# Add imports for text extraction
import PyPDF2
import docx
from PIL import Image
import pytesseract

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

@dataclass
class Message:
    content: str
    type: MessageType
    metadata: Optional[Dict] = None
    timestamp: datetime = datetime.now()
    sender: str = "bot"

class ConversationMemory:
    def __init__(self, max_messages: int = 50):
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.context_window = 8192  # Gemma 2 27B context window
        self.current_topics: List[str] = []
        self.user_preferences: Dict = {}
        self.conversation_context: Dict = {
            'topics': set(),
            'skills_mentioned': set(),
            'companies_mentioned': set(),
            'current_focus': None
        }
    
    def add_message(self, message: Message):
        """Add message and update context"""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        
        if message.type == MessageType.TEXT:
            self._update_context(message.content)
    
    def _update_context(self, content: str):
        """Update conversation context based on content"""
        content_lower = content.lower()
        
        # Update topics
        topics = {
            'technical': ['algorithm', 'coding', 'programming', 'system design', 'development'],
            'interview': ['interview', 'questions', 'preparation', 'practice'],
            'career': ['career', 'growth', 'path', 'future', 'goals'],
            'skills': ['skills', 'learning', 'technology', 'tools'],
            'companies': ['company', 'organization', 'workplace', 'employer'],
            'placement': ['placement', 'job', 'position', 'opportunity']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in content_lower for keyword in keywords):
                self.conversation_context['topics'].add(topic)
        
        # Update skills mentioned
        skills = [
            'python', 'java', 'javascript', 'react', 'node', 'sql',
            'machine learning', 'ai', 'cloud', 'aws', 'azure',
            'system design', 'algorithms', 'data structures'
        ]
        
        for skill in skills:
            if skill in content_lower:
                self.conversation_context['skills_mentioned'].add(skill)
        
        # Update companies mentioned
        companies = [
            'google', 'microsoft', 'amazon', 'meta', 'apple',
            'netflix', 'uber', 'twitter', 'linkedin'
        ]
        
        for company in companies:
            if company in content_lower:
                self.conversation_context['companies_mentioned'].add(company)
        
        # Determine current focus
        focus_indicators = {
            'technical': ['how to', 'example', 'code', 'implement'],
            'conceptual': ['explain', 'what is', 'understand', 'concept'],
            'practical': ['apply', 'use', 'practice', 'real world'],
            'career': ['career', 'job', 'future', 'growth']
        }
        
        for focus, indicators in focus_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                self.conversation_context['current_focus'] = focus
                break
    
    def get_formatted_context(self) -> str:
        """Get formatted context for the model"""
        context_parts = []
        
        # Add conversation focus
        if self.conversation_context['current_focus']:
            context_parts.append(
                f"Current focus: {self.conversation_context['current_focus']}"
            )
        
        # Add active topics
        if self.conversation_context['topics']:
            context_parts.append(
                f"Active topics: {', '.join(self.conversation_context['topics'])}"
            )
        
        # Add skills context if relevant
        if self.conversation_context['skills_mentioned']:
            context_parts.append(
                f"Skills discussed: {', '.join(self.conversation_context['skills_mentioned'])}"
            )
        
        # Add company context if relevant
        if self.conversation_context['companies_mentioned']:
            context_parts.append(
                f"Companies mentioned: {', '.join(self.conversation_context['companies_mentioned'])}"
            )
        
        # Add recent conversation
        if self.messages:
            context_parts.append("\nRecent conversation:")
            for msg in self.messages[-3:]:  # Last 3 messages
                sender = "User" if msg.sender == "user" else "Assistant"
                context_parts.append(f"{sender}: {msg.content}")
        
        return "\n".join(context_parts)

class PlacementData:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.categories = {
            'companies': self._load_json('companies.json'),
            'skills': self._load_json('skills.json'),
            # 'faqs': pd.read_csv(self.data_dir / 'faq.csv'),
            'courses': self._load_json('courses.json'),
            'interviews': self._load_json('interviews.json')
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
        self.memory = ConversationMemory()
        self.placement_data = PlacementData()
        
        # System prompt optimized for Gemma 2 27B
        self.system_prompt = """You are Atlas SkillTech University's advanced AI Placement Assistant, powered by Gemma 2 27B. 
You provide comprehensive, contextually aware assistance for placement preparation and career guidance.

Core Capabilities:
1. Technical Preparation
   - DSA and coding guidance
   - System design concepts
   - Technology stack advice
   - Best practices and patterns
   - Code review and optimization

2. Interview Excellence
   - Technical interview strategies
   - HR interview preparation
   - Company-specific insights
   - Mock interview simulation
   - STAR method application

3. Career Strategy
   - Industry trends analysis
   - Career path planning
   - Skill gap assessment
   - Growth opportunity identification
   - Technology adoption guidance

4. Placement Support
   - Application strategies
   - Resume optimization
   - Company research
   - Role-specific preparation
   - Salary negotiation tips

Communication Style:
- Professional yet approachable
- Clear and structured responses
- Examples and analogies when helpful
- Step-by-step explanations
- Contextually aware interactions

Special Instructions:
1. Maintain conversation context
2. Provide actionable advice
3. Use relevant examples
4. Break down complex topics
5. Format responses appropriately

Remember:
- Stay focused on placement and career
- Provide accurate technical information
- Be encouraging and supportive
- Acknowledge limitations when appropriate
- Maintain professional boundaries"""

    def get_response(self, query: str) -> Generator[Message, None, None]:
        """Generate streaming response with enhanced features"""
        try:
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
                yield Message(suggestions, MessageType.SUGGESTION)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield Message(
                f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                MessageType.ERROR
            )

    def prepare_response_prompt(self, query: str) -> str:
        """Prepare prompt for the text model"""
        # Start with the system prompt
        prompt = self.system_prompt

        # Include conversation context
        context = self.memory.get_formatted_context()
        if context:
            prompt += f"\n\nConversation Context:\n{context}"

        # Include format instructions
        format_instructions = self._get_format_instructions()
        if format_instructions:
            prompt += f"\n\n{format_instructions}"

        # Include the user's query
        prompt += f"\n\nUser Query: {query}"

        return prompt

    def _get_format_instructions(self) -> str:
        """Get response format instructions"""
        current_focus = self.memory.conversation_context['current_focus']
        
        instructions = ["Response Instructions:"]

        if current_focus == 'technical':
            instructions.extend([
                "- Provide code examples in markdown format",
                "- Include best practices and patterns",
                "- Add relevant technical explanations",
                "- Suggest resources for further learning"
            ])
        elif current_focus == 'interview':
            instructions.extend([
                "- Structure response in interview format",
                "- Include example Q&A pairs",
                "- Add interviewer perspectives",
                "- Provide preparation tips"
            ])
        elif current_focus == 'career':
            instructions.extend([
                "- Offer strategic career advice",
                "- Include industry insights",
                "- Suggest skill development paths",
                "- Provide actionable steps"
            ])
        else:
            instructions.extend([
                "- Structure response clearly",
                "- Include relevant examples",
                "- Add practical tips",
                "- Suggest next steps"
            ])
        
        return "\n".join(instructions)

    def _get_message_metadata(self, message: str, msg_type: MessageType) -> Dict:
        """Generate rich metadata for messages"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'type': msg_type.value
        }

        # Additional metadata processing can be added here

        return metadata

    def _generate_suggestions(self, query: str, response: str) -> List[str]:
        """Generate contextual follow-up suggestions"""
        suggestions = []

        # Topic-based suggestions
        if 'technical' in self.memory.conversation_context['topics']:
            suggestions.extend([
                "Can you provide more coding examples?",
                "What are the best practices for this?",
                "How can I practice these concepts?"
            ])
        
        if 'interview' in self.memory.conversation_context['topics']:
            suggestions.extend([
                "What are common follow-up questions?",
                "How should I handle behavioral questions?",
                "Can we do a mock interview?"
            ])
        
        if 'career' in self.memory.conversation_context['topics']:
            suggestions.extend([
                "What skills should I focus on next?",
                "How can I prepare for this role?",
                "What are the growth opportunities?"
            ])
        
        # Company-specific suggestions
        companies = self.memory.conversation_context['companies_mentioned']
        if companies:
            company = list(companies)[0]
            suggestions.extend([
                f"What is {company.title()}'s interview process?",
                f"What skills does {company.title()} value?",
                f"How can I prepare for {company.title()}?"
            ])
        
        # Skill-based suggestions
        skills = self.memory.conversation_context['skills_mentioned']
        if skills:
            skill = list(skills)[0]
            suggestions.extend([
                f"How can I master {skill}?",
                f"What projects can I build with {skill}?",
                f"Which companies value {skill}?"
            ])
        
        # Randomize and limit suggestions
        if suggestions:
            suggestions = list(set(suggestions))  # Remove duplicates
            suggestions = sorted(suggestions, key=lambda _: random.random())
            suggestions = suggestions[:3]  # Limit to 3 suggestions
        
        return suggestions

    # Implement methods to extract text from different file types
    def extract_text_from_pdf(self, uploaded_file) -> str:
        """Extract text from uploaded PDF file"""
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
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
        """Extract text from uploaded image file"""
        try:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
