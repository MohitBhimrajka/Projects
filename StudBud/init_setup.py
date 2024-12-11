import os
from pathlib import Path
import shutil
import json
import logging
import sys
import subprocess
import requests
import pandas as pd
from datetime import datetime
import platform
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('setup.log')
    ]
)
logger = logging.getLogger(__name__)

class SetupManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.required_dirs = [
            'data',
            'data/backups',
            'data/cache',
            'static',
            'static/images',
            'pages',
            'backend'
        ]
        self.required_files = {
            'data/jobs.csv': self._create_jobs_csv,
            'data/faq.csv': self._create_faq_csv,
            'data/users.csv': self._create_users_csv,
            'data/applications.csv': self._create_applications_csv,
            'data/companies.json': self._create_companies_json,
            'data/skills.json': self._create_skills_json,
            'data/courses.json': self._create_courses_json,
            'data/interviews.json': self._create_interviews_json
        }
        self.required_packages = [
            'streamlit',
            'pandas',
            'plotly',
            'jwt',
            'python-dotenv',
            'ollama',
            'numpy',
            'requests'
        ]
        self.model_name = "gemma2:27b"
    
    def setup(self) -> bool:
        """Run all setup checks and initialization"""
        try:
            logger.info("Starting setup process...")
            
            # Check Python version
            if not self._check_python_version():
                return False
            
            # Load environment variables
            self._setup_environment()
            
            # Create directory structure
            self._create_directories()
            
            # Check Python dependencies
            if not self._check_dependencies():
                return False
            
            # Check Ollama setup
            if not self._check_ollama():
                return False
            
            # Initialize data files
            self._initialize_data_files()
            
            # Verify setup
            if self._verify_setup():
                logger.info("Setup completed successfully!")
                return True
            else:
                logger.error("Setup verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False
    
    def _check_python_version(self) -> bool:
        """Check if Python version meets requirements"""
        required_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version >= required_version:
            logger.info(f"Python version {'.'.join(map(str, current_version))} OK")
            return True
        else:
            logger.error(
                f"Python version {'.'.join(map(str, required_version))} or higher required"
            )
            return False
    
    def _setup_environment(self):
        """Setup environment variables"""
        env_file = self.root_dir / '.env'
        env_example = self.root_dir / '.env.example'
        
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
            logger.info("Created .env file from template")
        
        load_dotenv()
        logger.info("Loaded environment variables")
    
    def _create_directories(self):
        """Create required directories"""
        for directory in self.required_dirs:
            dir_path = self.root_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def _check_dependencies(self) -> bool:
        """Verify all required Python packages are installed"""
        missing_packages = []
        
        for package in self.required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Installing missing packages...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', *missing_packages
                ])
                logger.info("Successfully installed missing packages")
                return True
            except subprocess.CalledProcessError:
                logger.error("Failed to install missing packages")
                return False
        
        logger.info("All required packages are installed")
        return True
    
    def _check_ollama(self) -> bool:
        """Check Ollama installation and model availability"""
        try:
            # Check if Ollama is installed
            try:
                subprocess.run(['ollama', '--version'], 
                             check=True, 
                             capture_output=True)
                logger.info("Ollama is installed")
            except subprocess.CalledProcessError:
                logger.error("Ollama is not installed")
                logger.info("Please install Ollama from: https://ollama.ai/download")
                return False

            # Start Ollama service if needed
            if not self._start_ollama_service():
                return False

            # Check for model
            try:
                result = subprocess.run(
                    ['ollama', 'list'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if self.model_name not in result.stdout:
                    logger.warning(f"{self.model_name} model not found")
                    logger.info(f"Pulling {self.model_name} model...")
                    pull_result = subprocess.run(
                        ['ollama', 'pull', self.model_name],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logger.info(f"{self.model_name} model installed successfully")
                else:
                    logger.info(f"{self.model_name} model is already installed")
                
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to check/pull model: {e.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error in Ollama setup: {str(e)}")
            return False

    def _start_ollama_service(self) -> bool:
        """Start the Ollama service if it's not running"""
        try:
            # Check if service is already running
            try:
                requests.get("http://localhost:11434/api/tags")
                logger.info("Ollama service is already running")
                return True
            except:
                logger.info("Starting Ollama service...")

            # Start Ollama service
            if platform.system() == "Windows":
                subprocess.Popen(
                    ['ollama', 'serve'],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                subprocess.Popen(
                    ['ollama', 'serve'],
                    start_new_session=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            # Wait for service to start
            retries = 5
            while retries > 0:
                try:
                    requests.get("http://localhost:11434/api/tags")
                    logger.info("Ollama service started successfully")
                    return True
                except:
                    time.sleep(2)
                    retries -= 1

            logger.error("Failed to start Ollama service")
            return False

        except Exception as e:
            logger.error(f"Error starting Ollama service: {str(e)}")
            return False
        
    def _create_jobs_csv(self, path: Path):
        """Create jobs.csv with initial data"""
        jobs_data = [
            {
                'job_id': 'JOB_001',
                'company': 'Google',
                'title': 'Software Engineer',
                'description': 'Join our dynamic team to work on cutting-edge technology projects.',
                'requirements': '["Python", "Distributed Systems", "Algorithms", "System Design"]',
                'salary_range': '30-60 LPA',
                'location': 'Bangalore',
                'job_type': 'Full-time',
                'posted_date': '2024-03-15',
                'deadline': '2024-04-15',
                'status': 'Open'
            },
            {
                'job_id': 'JOB_002',
                'company': 'Microsoft',
                'title': 'Senior ML Engineer',
                'description': 'Lead ML initiatives and develop innovative AI solutions.',
                'requirements': '["Python", "TensorFlow", "PyTorch", "MLOps"]',
                'salary_range': '40-70 LPA',
                'location': 'Hyderabad',
                'job_type': 'Full-time',
                'posted_date': '2024-03-15',
                'deadline': '2024-04-15',
                'status': 'Open'
            },
            {
                'job_id': 'JOB_003',
                'company': 'Amazon',
                'title': 'Full Stack Developer',
                'description': 'Build scalable web applications and services.',
                'requirements': '["React", "Node.js", "AWS", "MongoDB"]',
                'salary_range': '25-45 LPA',
                'location': 'Bangalore',
                'job_type': 'Full-time',
                'posted_date': '2024-03-15',
                'deadline': '2024-04-15',
                'status': 'Open'
            }
        ]
        df = pd.DataFrame(jobs_data)
        df.to_csv(path, index=False)
        logger.info(f"Created {path}")

    def _create_faq_csv(self, path: Path):
        """Create faq.csv with initial data"""
        faq_data = [
            {
                'question': 'What is the placement process at Atlas SkillTech?',
                'answer': 'The placement process includes: registration, aptitude tests, technical interviews, and HR rounds. Companies visit throughout the year.',
                'keywords': 'placement, process, registration, interview'
            },
            {
                'question': 'How should I prepare for technical interviews?',
                'answer': 'Focus on: 1) Data Structures & Algorithms 2) System Design 3) Programming fundamentals 4) Project work 5) Mock interviews',
                'keywords': 'technical, interview, preparation, coding'
            },
            {
                'question': 'What are the eligibility criteria for placements?',
                'answer': 'Students need: 1) Minimum 7.5 CGPA 2) No active backlogs 3) 75% attendance 4) Required technical skills',
                'keywords': 'eligibility, criteria, requirements, cgpa'
            }
        ]
        df = pd.DataFrame(faq_data)
        df.to_csv(path, index=False)
        logger.info(f"Created {path}")

    def _create_users_csv(self, path: Path):
        """Create users.csv with initial data"""
        users_data = [
            {
                'user_id': 'ADM001',
                'email': 'admin@atlas.edu',
                'password_hash': 'hashed_password_here',
                'salt': 'salt_here',
                'role': 'admin',
                'name': 'Admin User',
                'department': 'Administration',
                'year': 'NA',
                'created_at': '2024-03-15',
                'last_login': '2024-03-15'
            },
            {
                'user_id': 'STU001',
                'email': 'student@atlas.edu',
                'password_hash': 'hashed_password_here',
                'salt': 'salt_here',
                'role': 'student',
                'name': 'John Doe',
                'department': 'Computer Science',
                'year': 'Third Year',
                'created_at': '2024-03-15',
                'last_login': '2024-03-15'
            }
        ]
        df = pd.DataFrame(users_data)
        df.to_csv(path, index=False)
        logger.info(f"Created {path}")

    def _create_applications_csv(self, path: Path):
        """Create applications.csv with initial data"""
        applications_data = [
            {
                'application_id': 'APP001',
                'job_id': 'JOB_001',
                'user_id': 'STU001',
                'status': 'Under Review',
                'applied_date': '2024-03-15',
                'resume_path': 'resumes/STU001/resume.pdf',
                'cover_letter': 'I am excited to apply for this position...',
                'additional_info': '{"skills": ["Python", "Java"], "references": ["Prof. Smith"]}'
            }
        ]
        df = pd.DataFrame(applications_data)
        df.to_csv(path, index=False)
        logger.info(f"Created {path}")

    def _create_companies_json(self, path: Path):
        """Create companies.json with initial data"""
        companies_data = {
            'companies': [
                {
                    'name': 'Google',
                    'info': {
                        'industry': 'Technology',
                        'headquarters': 'Mountain View, CA',
                        'website': 'google.com',
                        'founded': 1998
                    },
                    'interview_process': {
                        'rounds': [
                            'Online Assessment',
                            'Technical Phone Screen',
                            'Virtual Onsite (4-5 rounds)',
                            'Team Matching'
                        ],
                        'focus_areas': [
                            'Data Structures',
                            'Algorithms',
                            'System Design',
                            'Coding'
                        ]
                    },
                    'tech_stack': [
                        'Python', 'Java', 'Go', 'C++',
                        'Kubernetes', 'TensorFlow'
                    ]
                }
            ]
        }
        with open(path, 'w') as f:
            json.dump(companies_data, f, indent=2)
        logger.info(f"Created {path}")

    def _create_skills_json(self, path: Path):
        """Create skills.json with initial data"""
        skills_data = {
            'technical_skills': {
                'programming_languages': [
                    {
                        'name': 'Python',
                        'topics': [
                            'Data Structures',
                            'OOP',
                            'Web Frameworks',
                            'Data Science'
                        ]
                    },
                    {
                        'name': 'Java',
                        'topics': [
                            'Core Java',
                            'Spring Boot',
                            'Microservices',
                            'Multithreading'
                        ]
                    }
                ],
                'web_technologies': [
                    'React',
                    'Angular',
                    'Node.js',
                    'Django'
                ],
                'databases': [
                    'MySQL',
                    'MongoDB',
                    'PostgreSQL',
                    'Redis'
                ]
            },
            'soft_skills': [
                'Communication',
                'Team Collaboration',
                'Problem Solving',
                'Leadership'
            ]
        }
        with open(path, 'w') as f:
            json.dump(skills_data, f, indent=2)
        logger.info(f"Created {path}")

    def _create_courses_json(self, path: Path):
        """Create courses.json with initial data"""
        courses_data = {
            'preparation_courses': [
                {
                    'title': 'DSA Masterclass',
                    'duration': '8 weeks',
                    'topics': [
                        'Arrays and Strings',
                        'Trees and Graphs',
                        'Dynamic Programming',
                        'System Design'
                    ],
                    'resources': [
                        'LeetCode Premium',
                        'GeeksForGeeks',
                        'System Design Primer'
                    ]
                },
                {
                    'title': 'Interview Preparation',
                    'duration': '4 weeks',
                    'topics': [
                        'Resume Building',
                        'Mock Interviews',
                        'HR Interview Skills',
                        'Communication'
                    ]
                }
            ]
        }
        with open(path, 'w') as f:
            json.dump(courses_data, f, indent=2)
        logger.info(f"Created {path}")

    def _create_interviews_json(self, path: Path):
        """Create interviews.json with initial data"""
        interviews_data = {
            'technical_questions': [
                {
                    'type': 'DSA',
                    'difficulty': 'Medium',
                    'question': 'Implement a balanced binary search tree',
                    'topics': ['Trees', 'BST', 'Balancing'],
                    'companies': ['Google', 'Microsoft', 'Amazon']
                }
            ],
            'hr_questions': [
                {
                    'category': 'Leadership',
                    'question': 'Tell me about a time you led a difficult project',
                    'tips': [
                        'Use STAR method',
                        'Focus on team collaboration',
                        'Highlight results'
                    ]
                }
            ],
            'interview_tips': [
                {
                    'phase': 'Before Interview',
                    'tips': [
                        'Research the company',
                        'Review job description',
                        'Prepare STAR stories',
                        'Practice coding'
                    ]
                }
            ]
        }
        with open(path, 'w') as f:
            json.dump(interviews_data, f, indent=2)
        logger.info(f"Created {path}")

    def _initialize_data_files(self):
        """Initialize all required data files if they don't exist"""
        for file_path, creator_func in self.required_files.items():
            full_path = self.root_dir / file_path
            if not full_path.exists():
                logger.info(f"Creating {file_path}")
                creator_func(full_path)
            else:
                logger.info(f"File exists: {file_path}")
    
    def _verify_setup(self) -> bool:
        """Verify all components are properly set up"""
        success = True
        
        # Check directories
        logger.info("Verifying directories...")
        for directory in self.required_dirs:
            dir_path = self.root_dir / directory
            if not dir_path.is_dir():
                logger.error(f"Directory not found: {directory}")
                success = False
            else:
                logger.info(f"✓ Directory verified: {directory}")
        
        # Check files
        logger.info("Verifying data files...")
        for file_path in self.required_files:
            full_path = self.root_dir / file_path
            if not full_path.is_file():
                logger.error(f"File not found: {file_path}")
                success = False
            else:
                logger.info(f"✓ File exists: {file_path}")
        
        # Verify file contents
        logger.info("Verifying file contents...")
        try:
            # Verify CSV files
            csv_files = {
                'jobs.csv': {'required_cols': ['job_id', 'company', 'title']},
                'faq.csv': {'required_cols': ['question', 'answer']},
                'users.csv': {'required_cols': ['user_id', 'email', 'role']},
                'applications.csv': {'required_cols': ['application_id', 'job_id', 'user_id']}
            }
            
            for csv_file, requirements in csv_files.items():
                file_path = self.root_dir / 'data' / csv_file
                df = pd.read_csv(file_path)
                missing_cols = [col for col in requirements['required_cols'] if col not in df.columns]
                if missing_cols:
                    logger.error(f"Missing columns in {csv_file}: {missing_cols}")
                    success = False
                else:
                    logger.info(f"✓ Verified {csv_file} structure")
            
            # Verify JSON files
            json_files = ['companies.json', 'skills.json', 'courses.json', 'interviews.json']
            for json_file in json_files:
                file_path = self.root_dir / 'data' / json_file
                with open(file_path) as f:
                    data = json.load(f)
                    if not data:
                        logger.error(f"Empty JSON file: {json_file}")
                        success = False
                    else:
                        logger.info(f"✓ Verified {json_file} content")
            
        except Exception as e:
            logger.error(f"File verification failed: {e}")
            success = False
        
        return success
    
    def _verify_environment(self) -> bool:
        """Verify environment setup"""
        required_env_vars = [
            'APP_NAME',
            'DEBUG',
            'SECRET_KEY',
            'JWT_SECRET',
            'OLLAMA_HOST',
            'MODEL_NAME'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing environment variables: {missing_vars}")
            return False
        
        logger.info("✓ Environment variables verified")
        return True
    
    def _create_default_env(self):
        """Create default .env file if not exists"""
        env_path = self.root_dir / '.env'
        if not env_path.exists():
            default_env = f"""# Application Settings
APP_NAME="Atlas SkillTech Placement Assistant"
DEBUG=True
ENVIRONMENT=development

# Security
SECRET_KEY={os.urandom(24).hex()}
JWT_SECRET={os.urandom(24).hex()}
JWT_EXPIRY=12

# Ollama Settings
OLLAMA_HOST=http://localhost:11434
MODEL_NAME={self.model_name}
CONTEXT_LENGTH=8192

# Feature Flags
ENABLE_CHAT_HISTORY=true
ENABLE_NOTIFICATIONS=true
ENABLE_ANALYTICS=true
"""
            with open(env_path, 'w') as f:
                f.write(default_env)
            logger.info("Created default .env file")

def print_banner():
    """Print setup banner"""
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║     Atlas SkillTech Placement Assistant       ║
    ║              Setup Utility                    ║
    ╚═══════════════════════════════════════════════╝
    """
    print(banner)

def print_success_message():
    """Print success message with next steps"""
    success_msg = """
    ✨ Setup completed successfully! ✨

    Next steps:
    1. Start Ollama service (if not running):
       ollama serve

    2. In a new terminal, activate your environment:
       source studbud/bin/activate

    3. Start the application:
       streamlit run app.py

    4. Test the chatbot:
       ollama run gemma2:27b

    For more information, check the README.md file.
    """
    print(success_msg)

def print_error_message():
    """Print error message with troubleshooting steps"""
    error_msg = """
    ❌ Setup failed! Please check:

    1. Python environment and dependencies
    2. Ollama installation and service status
    3. File permissions in the project directory
    4. Log file (setup.log) for detailed errors

    Try running the setup again after fixing the issues.
    For help, consult the README.md or contact support.
    """
    print(error_msg)

def main():
    """Run setup process"""
    print_banner()
    
    try:
        setup_manager = SetupManager()
        
        logger.info("Starting setup process...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {platform.platform()}")
        
        if setup_manager.setup():
            print_success_message()
            return 0
        else:
            print_error_message()
            return 1
            
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print_error_message()
        return 1

if __name__ == "__main__":
    sys.exit(main())