# AI Admission Inquiry Assistant

A comprehensive AI-powered chatbot system for handling university admission inquiries through text and voice interactions. Built with Python Flask backend and React frontend.

## 🚀 Features

### Core Functionality
- **Text Chat Interface**: Natural language conversation with AI assistant
- **Voice Interaction**: Speech-to-text and text-to-speech capabilities  
- **Intent Recognition**: Advanced NLU for understanding user queries
- **Knowledge Retrieval**: Semantic search through admission information
- **Follow-up Emails**: Automated email responses and reminders
- **Analytics Dashboard**: Comprehensive usage statistics and insights

### AI Capabilities
- **Speech Recognition**: OpenAI Whisper for accurate transcription
- **Natural Language Understanding**: Custom intent classification
- **Response Generation**: Context-aware dialogue management
- **Text-to-Speech**: Coqui TTS for voice responses
- **Semantic Search**: ChromaDB with sentence transformers

### Additional Features
- **Multi-modal Support**: Both chat and voice interfaces
- **Real-time Analytics**: Usage patterns and performance metrics
- **Responsive Design**: Mobile-friendly interface
- **Accessibility**: Screen reader and keyboard navigation support
- **Error Handling**: Robust error recovery and fallback responses

## 🛠 Tech Stack

### Backend
- **Framework**: Flask 2.3.3
- **AI/ML**: OpenAI Whisper, Transformers, Sentence Transformers
- **Database**: SQLite with ChromaDB for vector storage
- **TTS**: Coqui TTS
- **Email**: SMTP integration
- **Python**: 3.11.5 compatible

### Frontend  
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Notifications**: React Hot Toast

## 📋 Prerequisites

- Python 3.11.5 or higher
- Node.js 16.0.0 or higher
- npm 8.0.0 or higher
- Git

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd admission-inquiry-ai
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create environment file (optional)
cp .env.example .env.local
```

### 4. Configuration

#### Backend Configuration (backend/.env)
```env
# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Email Configuration (for follow-up emails)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=admissions@university.edu

# Logging
LOG_LEVEL=INFO
```

#### Initialize Database and Knowledge Base
```bash
cd backend
python -c "
from app import app
from utils.database import DatabaseManager
from agents.retrieval_agent import RetrievalAgent

with app.app_context():
    db = DatabaseManager()
    retrieval = RetrievalAgent()
    print('Database and knowledge base initialized!')
"
```

## 🚀 Running the Application

### Development Mode

#### Start Backend Server
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```
Backend will be available at: http://localhost:5000

#### Start Frontend Development Server
```bash
cd frontend
npm run dev
```
Frontend will be available at: http://localhost:3000

### Production Mode

#### Build Frontend
```bash
cd frontend
npm run build
```

#### Serve with Production Server
```bash
# Install production server (e.g., gunicorn)
pip install gunicorn

# Run backend with gunicorn
cd backend
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# Serve frontend (use nginx or similar in production)
cd frontend
npm run preview
```

## 📁 Project Structure

```
admission-inquiry-ai/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── config.py                 # Configuration settings
│   ├── requirements.txt          # Python dependencies
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── asr_agent.py         # Speech-to-Text
│   │   ├── nlu_agent.py         # Natural Language Understanding
│   │   ├── retrieval_agent.py   # Knowledge base retrieval
│   │   ├── dialogue_agent.py    # Response generation
│   │   ├── tts_agent.py         # Text-to-Speech
│   │   └── followup_agent.py    # Email follow-up
│   ├── data/
│   │   ├── knowledge_base.json  # FAQ and admission info
│   │   ├── intents.json         # NLU training data
│   │   └── chroma_db/           # Vector database
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLite operations
│   │   └── logger.py            # Logging utilities
│   ├── models/                  # Trained models
│   ├── logs/                    # Application logs
│   └── uploads/                 # Temporary files
├── frontend/
│   ├── index.html               # Main HTML file
│   ├── package.json             # Node.js dependencies
│   ├── vite.config.js           # Vite configuration
│   ├── tailwind.config.js       # Tailwind configuration
│   ├── postcss.config.js        # PostCSS configuration
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── main.jsx             # React entry point
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx    # Chat UI
│   │   │   ├── VoiceInterface.jsx   # Voice UI
│   │   │   └── Analytics.jsx       # Analytics dashboard
│   │   └── styles/
│   │       └── index.css        # Main styles
└── README.md                    # This file
```

## 🔧 Configuration

### Customizing the Knowledge Base

Edit `backend/data/knowledge_base.json` to update:
- University information
- FAQ content
- Contact details
- Program information

### Adding New Intents

Edit `backend/data/intents.json` to add:
- New conversation intents
- Training examples
- Intent patterns

### Email Templates

Modify email templates in `backend/agents/followup_agent.py`:
- Welcome messages
- Follow-up content
- University branding

## 📊 API Endpoints

### Chat API
```http
POST /chat
Content-Type: application/json

{
  "message": "What are the admission requirements?",
  "session_id": "session_123"
}
```

### Voice API
```http
POST /voice
Content-Type: multipart/form-data

audio: [audio file]
session_id: session_123
```

### Analytics API
```http
GET /analytics?days=7
```

### Follow-up API
```http
POST /followup
Content-Type: application/json

{
  "email": "student@example.com",
  "name": "John Doe",
  "session_id": "session_123",
  "inquiry_type": "general"
}
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Manual Testing
1. Start both backend and frontend servers
2. Test chat functionality with sample questions
3. Test voice recording (requires microphone access)
4. Check analytics dashboard
5. Test follow-up email functionality

## 🚀 Deployment

### Using Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individual containers
cd backend
docker build -t admission-ai-backend .

cd frontend
docker build -t admission-ai-frontend .
```

### Manual Deployment

1. **Backend Deployment**:
   - Use gunicorn or uwsgi for production WSGI server
   - Configure nginx for reverse proxy
   - Set up SSL certificates
   - Configure environment variables

2. **Frontend Deployment**:
   - Build production bundle: `npm run build`
   - Serve with nginx or similar
   - Configure CDN for static assets

3. **Database**:
   - For production, consider PostgreSQL instead of SQLite
   - Set up regular backups
   - Monitor database performance

## 📈 Performance Optimization

### Backend Optimizations
- Enable Redis for caching
- Use connection pooling for database
- Implement request rate limiting
- Optimize model loading and inference

### Frontend Optimizations
- Enable code splitting
- Implement lazy loading for components
- Optimize bundle size
- Use service workers for caching

## 🔒 Security Considerations

### Backend Security
- Input validation and sanitization
- Rate limiting for API endpoints
- CORS configuration
- Environment variable protection
- SQL injection prevention

### Frontend Security
- XSS prevention
- Content Security Policy
- HTTPS enforcement
- Secure cookie handling

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues
1. **Module Import Errors**:
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database file permissions
   chmod 664 backend/data/admission_assistant.db
   ```

3. **Audio Processing Errors**:
   ```bash
   # Install additional audio dependencies
   pip install ffmpeg-python
   # On Linux: sudo apt-get install ffmpeg
   # On macOS: brew install ffmpeg
   ```

#### Frontend Issues
1. **Build Errors**:
   ```bash
   # Clear node modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **CORS Issues**:
   - Check that backend CORS is properly configured
   - Verify API endpoints are accessible

### Debug Mode
```bash
# Backend debug mode
export FLASK_DEBUG=1
python app.py

# Frontend debug mode
npm run dev
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the documentation wiki

## 🙏 Acknowledgments

- OpenAI Whisper for speech recognition
- Hugging Face for transformer models
- Coqui TTS for text-to-speech
- ChromaDB for vector storage
- React and Tailwind CSS communities

---

**Version**: 1.0.0  
**Last Updated**: 2024