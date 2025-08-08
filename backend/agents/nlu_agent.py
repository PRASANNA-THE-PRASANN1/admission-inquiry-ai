import json
import re
import logging
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pickle
import os

from ..config import INTENTS_PATH, CONFIDENCE_THRESHOLD, BASE_DIR

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class NLUAgent:
    """Natural Language Understanding Agent for Intent Classification and Entity Extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Intent classification pipeline
        self.intent_classifier = None
        self.intent_labels = []
        
        # Entity patterns
        self.entity_patterns = {}
        
        # Load intents and train model
        self.load_intents()
        self.train_intent_classifier()
        self.setup_entity_patterns()
    
    def load_intents(self):
        """Load intent training data"""
        try:
            if os.path.exists(INTENTS_PATH):
                with open(INTENTS_PATH, 'r') as f:
                    self.intents_data = json.load(f)
                self.logger.info("Intent data loaded successfully")
            else:
                # Create default intents if file doesn't exist
                self.create_default_intents()
                
        except Exception as e:
            self.logger.error(f"Error loading intents: {e}")
            self.create_default_intents()
    
    def create_default_intents(self):
        """Create default intent training data"""
        default_intents = {
            "intents": [
                {
                    "tag": "admission_requirements",
                    "patterns": [
                        "What are the admission requirements?",
                        "admission criteria",
                        "requirements for admission",
                        "what do I need to apply",
                        "eligibility criteria",
                        "admission qualifications",
                        "entry requirements"
                    ]
                },
                {
                    "tag": "application_deadline",
                    "patterns": [
                        "When is the application deadline?",
                        "deadline for applications",
                        "last date to apply",
                        "application due date",
                        "when should I apply",
                        "application timeline"
                    ]
                },
                {
                    "tag": "tuition_fees",
                    "patterns": [
                        "What are the tuition fees?",
                        "cost of education",
                        "fees structure",
                        "how much does it cost",
                        "tuition costs",
                        "education expenses",
                        "fee details"
                    ]
                },
                {
                    "tag": "programs_offered",
                    "patterns": [
                        "What programs do you offer?",
                        "available courses",
                        "list of programs",
                        "majors available",
                        "degree programs",
                        "course offerings",
                        "academic programs"
                    ]
                },
                {
                    "tag": "financial_aid",
                    "patterns": [
                        "Financial aid options",
                        "scholarships available",
                        "student loans",
                        "grants and scholarships",
                        "financial assistance",
                        "funding options"
                    ]
                },
                {
                    "tag": "contact_info",
                    "patterns": [
                        "How can I contact admissions?",
                        "admissions office contact",
                        "phone number",
                        "email address",
                        "contact details",
                        "get in touch"
                    ]
                },
                {
                    "tag": "campus_visit",
                    "patterns": [
                        "Can I visit the campus?",
                        "campus tour",
                        "visit the university",
                        "campus visits",
                        "schedule a tour"
                    ]
                },
                {
                    "tag": "housing",
                    "patterns": [
                        "Student housing options",
                        "dormitories",
                        "accommodation",
                        "residence halls",
                        "on-campus housing"
                    ]
                },
                {
                    "tag": "greeting",
                    "patterns": [
                        "Hello",
                        "Hi",
                        "Good morning",
                        "Good afternoon",
                        "Hey",
                        "Greetings"
                    ]
                },
                {
                    "tag": "goodbye",
                    "patterns": [
                        "Goodbye",
                        "Bye",
                        "Thank you",
                        "Thanks",
                        "See you later"
                    ]
                }
            ]
        }
        
        # Save default intents
        with open(INTENTS_PATH, 'w') as f:
            json.dump(default_intents, f, indent=2)
        
        self.intents_data = default_intents
        self.logger.info("Default intents created")
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for NLU"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        processed_tokens = []
        for token in tokens:
            if token not in self.stop_words and len(token) > 2:
                lemmatized = self.lemmatizer.lemmatize(token)
                processed_tokens.append(lemmatized)
        
        return ' '.join(processed_tokens)
    
    def train_intent_classifier(self):
        """Train intent classification model"""
        try:
            training_texts = []
            training_labels = []
            
            for intent in self.intents_data.get('intents', []):
                tag = intent['tag']
                patterns = intent['patterns']
                
                for pattern in patterns:
                    processed_text = self.preprocess_text(pattern)
                    training_texts.append(processed_text)
                    training_labels.append(tag)
            
            if not training_texts:
                raise ValueError("No training data available")
            
            # Create unique labels
            self.intent_labels = list(set(training_labels))
            
            # Create and train pipeline
            self.intent_classifier = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
                ('classifier', MultinomialNB(alpha=0.1))
            ])
            
            self.intent_classifier.fit(training_texts, training_labels)
            
            # Save trained model
            model_path = BASE_DIR / 'models' / 'intent_classifier.pkl'
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'classifier': self.intent_classifier,
                    'labels': self.intent_labels
                }, f)
            
            self.logger.info(f"Intent classifier trained with {len(training_texts)} examples")
            
        except Exception as e:
            self.logger.error(f"Error training intent classifier: {e}")
            raise
    
    def setup_entity_patterns(self):
        """Setup regex patterns for entity extraction"""
        self.entity_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
            'date': re.compile(r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b|\\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', re.IGNORECASE),
            'gpa': re.compile(r'\b[0-4]\.\d{1,2}\b|\b[0-4]\s*GPA\b', re.IGNORECASE),
            'money': re.compile(r'\$[\d,]+(?:\.\d{2})?'),
            'program': re.compile(r'\b(?:computer science|engineering|business|medicine|law|arts|science|mathematics|physics|chemistry|biology|psychology|economics|english|history)\b', re.IGNORECASE)
        }
    
    def classify_intent(self, text: str) -> Dict:
        """Classify intent of input text"""
        try:
            if not self.intent_classifier:
                return {
                    'intent': 'unknown',
                    'confidence': 0.0,
                    'entities': self.extract_entities(text)
                }
            
            # Preprocess text
            processed_text = self.preprocess_text(text)
            
            # Predict intent
            predicted_intent = self.intent_classifier.predict([processed_text])[0]
            
            # Get confidence scores
            confidence_scores = self.intent_classifier.predict_proba([processed_text])[0]
            max_confidence = max(confidence_scores)
            
            # Extract entities
            entities = self.extract_entities(text)
            
            # Check confidence threshold
            if max_confidence < CONFIDENCE_THRESHOLD:
                predicted_intent = 'unknown'
                max_confidence = 0.0
            
            return {
                'intent': predicted_intent,
                'confidence': float(max_confidence),
                'entities': entities,
                'all_intents': dict(zip(self.intent_labels, confidence_scores.tolist()))
            }
            
        except Exception as e:
            self.logger.error(f"Error classifying intent: {e}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'entities': self.extract_entities(text),
                'error': str(e)
            }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        entities = {}
        
        try:
            for entity_type, pattern in self.entity_patterns.items():
                matches = pattern.findall(text)
                if matches:
                    if entity_type == 'phone':
                        # Format phone numbers
                        formatted_phones = []
                        for match in matches:
                            if isinstance(match, tuple):
                                formatted_phones.append(f"({match[0]}) {match[1]}-{match[2]}")
                            else:
                                formatted_phones.append(match)
                        entities[entity_type] = formatted_phones
                    else:
                        entities[entity_type] = matches if isinstance(matches[0], str) else [match[0] for match in matches]
            
            # Extract additional context-specific entities
            entities.update(self._extract_contextual_entities(text))
            
        except Exception as e:
            self.logger.error(f"Error extracting entities: {e}")
        
        return entities
    
    def _extract_contextual_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract context-specific entities"""
        contextual_entities = {}
        
        # Grade/Year extraction
        grade_pattern = re.compile(r'\b(?:freshman|sophomore|junior|senior|graduate|undergraduate|phd|masters?)\b', re.IGNORECASE)
        grades = grade_pattern.findall(text)
        if grades:
            contextual_entities['academic_level'] = grades
        
        # SAT/ACT scores
        sat_pattern = re.compile(r'\bSAT\s*:?\s*(\d{3,4})\b', re.IGNORECASE)
        act_pattern = re.compile(r'\bACT\s*:?\s*(\d{1,2})\b', re.IGNORECASE)
        
        sat_scores = sat_pattern.findall(text)
        act_scores = act_pattern.findall(text)
        
        if sat_scores:
            contextual_entities['sat_score'] = sat_scores
        if act_scores:
            contextual_entities['act_score'] = act_scores
        
        return contextual_entities
    
    def get_intent_confidence_breakdown(self, text: str) -> Dict:
        """Get detailed confidence breakdown for all intents"""
        try:
            processed_text = self.preprocess_text(text)
            
            if not self.intent_classifier:
                return {}
            
            confidence_scores = self.intent_classifier.predict_proba([processed_text])[0]
            
            # Create confidence breakdown
            breakdown = {}
            for label, score in zip(self.intent_labels, confidence_scores):
                breakdown[label] = {
                    'confidence': float(score),
                    'percentage': f"{score * 100:.1f}%"
                }
            
            # Sort by confidence
            sorted_breakdown = dict(sorted(breakdown.items(), key=lambda x: x[1]['confidence'], reverse=True))
            
            return sorted_breakdown
            
        except Exception as e:
            self.logger.error(f"Error getting confidence breakdown: {e}")
            return {}
    
    def add_training_example(self, text: str, intent: str):
        """Add new training example and retrain model"""
        try:
            # Find or create intent
            intent_found = False
            for intent_data in self.intents_data.get('intents', []):
                if intent_data['tag'] == intent:
                    intent_data['patterns'].append(text)
                    intent_found = True
                    break
            
            if not intent_found:
                # Create new intent
                self.intents_data.setdefault('intents', []).append({
                    'tag': intent,
                    'patterns': [text]
                })
            
            # Save updated intents
            with open(INTENTS_PATH, 'w') as f:
                json.dump(self.intents_data, f, indent=2)
            
            # Retrain classifier
            self.train_intent_classifier()
            
            self.logger.info(f"Added training example: '{text}' -> '{intent}'")
            
        except Exception as e:
            self.logger.error(f"Error adding training example: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.intent_classifier = None
        self.logger.info("NLU Agent cleaned up")