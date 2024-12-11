# Atlas SkillTech University - Placement Assistant

A comprehensive placement assistant system built with Streamlit and powered by Gemma 2B for intelligent career guidance and placement support.

## 🌟 Features

### 💼 Job Management
- Real-time job listings from top companies
- Advanced filtering and search capabilities
- Easy application process
- Application tracking system
- Company profiles and insights

### 🤖 AI Placement Assistant
- Powered by Gemma 27B through Ollama
- Interview preparation guidance
- Resume building and analysis using llama3.2:vision
- Career advice
- Company-specific insights
- Technical and HR interview preparation

### 📊 Applications Dashboard
- Track application status
- Interview schedules
- Application analytics
- Document management
- Communication history

### 👨‍💼 Admin Panel
- Comprehensive placement statistics
- Application management
- User management
- Analytics dashboard
- System configuration

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI Model**: Gemma 27B and Llama3.2:vision (via Ollama)
- **Data Storage**: CSV and JSON files
- **Authentication**: JWT-based system
- **Analytics**: Plotly
- **Styling**: Custom CSS

## 📁 Project Structure

```
studbud/
├── app.py              # Main Streamlit app
├── pages/
│   ├── Login.py        # Login system
│   ├── Home.py         # Job listings
│   ├── Chatbot.py      # Chatbot integration
│   ├── Applications.py # Student applications
│   └── Admin.py        # Admin dashboard
├── backend/
│   ├── chatbot.py      # Chatbot logic
│   ├── auth.py         # Authentication logic
│   ├── database.py     # Database handling
│   ├── jobs.py         # Job management
│   ├── applications.py # Application management
├── data/
│   ├── jobs.csv        # Job listings
│   ├── faq.csv         # FAQs for chatbot
│   ├── users.csv       # User credentials
│   ├── applications.csv # Application data
│   ├── companies.json  # Company details
│   ├── skills.json     # Skills database
│   ├── courses.json    # Course information
│   └── interviews.json # Interview resources
├── static/
│   ├── styles.css      # Global styles
│   └── images/         # Visual assets
├── requirements.txt    # Dependencies
└── README.md          # Documentation
```

## 🚀 Getting Started

1. **Set Up Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install Ollama**
   ```bash
   # Follow Ollama installation instructions for your OS
   # Pull Gemma 2B model
   ollama pull gemma:2b
   ```

3. **Run the Application**
   ```bash
   streamlit run app.py
   ```

## 🔐 Default Credentials

- **Admin Login**
  - Email: admin@atlas.edu
  - Password: admin123

- **Student Login**
  - Email: student@atlas.edu
  - Password: student123

## 💡 Usage

### For Students
1. Login with your credentials
2. Browse available job listings
3. Use AI assistant for guidance
4. Apply for positions
5. Track your applications
6. Prepare for interviews

### For Administrators
1. Login with admin credentials
2. Manage job listings
3. Review applications
4. Access analytics
5. Configure system settings

## 🤖 AI Assistant Features

The AI Placement Assistant provides:
- Resume review and suggestions
- Interview preparation
- Company research assistance
- Technical concept explanations
- Career path guidance
- Soft skills development tips

## 📊 Analytics

The system provides detailed analytics including:
- Placement statistics
- Company-wise distribution
- Application success rates
- Interview performance metrics
- Skill gap analysis

## 🔒 Security Features

- JWT-based authentication
- Role-based access control
- Secure password hashing
- Session management
- Input validation

## ⚠️ Prerequisites

- Python 3.8+
- Streamlit 1.29.0+
- Ollama
- Modern web browser
- Internet connection

## 🌐 Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## 💻 Development

For development setup:
1. Install development dependencies
2. Set up pre-commit hooks
3. Follow coding standards
4. Write tests
5. Update documentation

---
Built with ❤️ by Atlas SkillTech University Development Team