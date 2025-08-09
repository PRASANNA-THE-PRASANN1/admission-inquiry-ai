import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# API Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Database Configuration
DATABASE_PATH = BASE_DIR / 'data' / 'admission_assistant.db'

# Knowledge Base Configuration  
KNOWLEDGE_BASE_PATH = BASE_DIR / 'data' / 'knowledge_base.json'
INTENTS_PATH = BASE_DIR / 'data' / 'intents.json'

# ChromaDB Configuration
CHROMA_DB_PATH = BASE_DIR / 'data' / 'chroma_db'
COLLECTION_NAME = 'admission_knowledge'

# Model Configurations
WHISPER_MODEL = 'tiny'  # base, small, medium, large
TTS_MODEL = 'tts_models/en/ljspeech/tacotron2-DDC'

# Hugging Face Model Configuration
HF_MODEL_NAME = 'microsoft/DialoGPT-medium'  # Lightweight dialogue model
HF_CACHE_DIR = BASE_DIR / 'models' / 'hf_cache'

# File Upload Configuration
UPLOAD_FOLDER = BASE_DIR / 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'admission@university.edu')

# NLU Configuration
CONFIDENCE_THRESHOLD = 0.7
FALLBACK_RESPONSES = [
    "I understand you're asking about admissions. Let me connect you with our admissions office.",
    "For specific queries beyond my knowledge, please contact our admissions team at admissions@university.edu",
    "I'd be happy to help! Could you please rephrase your question?"
]

# Audio Configuration
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SIZE = 1024

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = BASE_DIR / 'logs' / 'admission_assistant.log'

# Ensure directories exist
for path in [DATABASE_PATH.parent, CHROMA_DB_PATH, HF_CACHE_DIR, UPLOAD_FOLDER, LOG_FILE.parent]:
    path.mkdir(parents=True, exist_ok=True)