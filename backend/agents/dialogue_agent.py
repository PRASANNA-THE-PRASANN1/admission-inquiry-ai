import logging
import random
from typing import Dict, List, Any
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from datetime import datetime
import re

from ..config import HF_MODEL_NAME, HF_CACHE_DIR, FALLBACK_RESPONSES

class DialogueAgent:
    """Dialogue Generation Agent using Hugging Face Transformers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.generator = None
        
        # Conversation context storage
        self.conversation_contexts = {}
        
        # Response templates
        self.response_templates = self._setup_response_templates()
        
        # Initialize model
        self.load_model()
    
    def load_model(self):
        """Load Hugging Face model for dialogue generation"""
        try:
            self.logger.info(f"Loading dialogue model: {HF_MODEL_NAME}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                HF_MODEL_NAME,
                cache_dir=HF_CACHE_DIR,
                padding_side='left'
            )
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                HF_MODEL_NAME,
                cache_dir=HF_CACHE_DIR,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            self.logger.info("Dialogue model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading dialogue model: {e}")
            self.logger.warning("Falling back to template-based responses")
            self.generator = None
    
    def _setup_response_templates(self):
        """Setup response templates for different intents"""
        return {
            'greeting': [
                "Hello! I'm here to help you with your admission inquiries. What would you like to know?",
                "Hi there! Welcome to our admissions assistant. How can I assist you today?",
                "Greetings! I'm ready to help you with any questions about our university. What's on your mind?"
            ],
            'goodbye': [
                "Thank you for using our admissions assistant! If you have more questions, feel free to ask anytime.",
                "Goodbye! Don't hesitate to reach out if you need more information about our programs.",
                "It was great helping you today! Good luck with your application process."
            ],
            'admission_requirements': [
                "Here are the admission requirements for our university:",
                "To apply for admission, you'll need the following:",
                "Our admission requirements include:"
            ],
            'application_deadline': [
                "Important deadline information:",
                "Here are the application deadlines you need to know:",
                "Please note these important dates:"
            ],
            'tuition_fees': [
                "Here's information about tuition and fees:",
                "The current fee structure is as follows:",
                "Cost information for our programs:"
            ],
            'programs_offered': [
                "We offer a wide range of programs:",
                "Here are the academic programs available:",
                "Our educational offerings include:"
            ],
            'financial_aid': [
                "Financial assistance options include:",
                "Here's information about financial aid:",
                "We offer several ways to help fund your education:"
            ],
            'contact_info': [
                "You can reach our admissions office through:",
                "Here's how to contact us:",
                "Our contact information:"
            ],
            'campus_visit': [
                "We'd love to have you visit our campus!",
                "Campus visit information:",
                "Here's how you can explore our campus:"
            ],
            'housing': [
                "Our housing options include:",
                "Here's information about student accommodation:",
                "Residential life at our university:"
            ],
            'unknown': [
                "I understand you're asking about admissions. Let me help you find the right information.",
                "That's a great question! Let me see what I can find for you.",
                "I want to make sure I give you accurate information. Could you please provide more details?"
            ]
        }
    
    def generate_response(self, user_input: str, intent_result: Dict, retrieved_info: Dict, session_id: str = "default") -> str:
        """Generate a response based on user input and context"""
        try:
            intent = intent_result.get('intent', 'unknown')
            confidence = intent_result.get('confidence', 0.0)
            
            # Update conversation context
            self._update_context(session_id, user_input, intent)
            
            # Get conversation context
            context = self._get_context(session_id)
            
            # Generate response based on available information
            if retrieved_info.get('documents') and confidence > 0.5:
                response = self._generate_informed_response(
                    user_input, intent, retrieved_info, context
                )
            else:
                response = self._generate_fallback_response(
                    user_input, intent, context
                )
            
            # Post-process response
            response = self._post_process_response(response, intent)
            
            # Update context with response
            context['responses'].append(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return random.choice(FALLBACK_RESPONSES)
    
    def _generate_informed_response(self, user_input: str, intent: str, retrieved_info: Dict, context: Dict) -> str:
        """Generate response using retrieved information"""
        try:
            documents = retrieved_info.get('documents', [])
            metadatas = retrieved_info.get('metadatas', [])
            
            if not documents:
                return self._generate_fallback_response(user_input, intent, context)
            
            # Extract relevant information
            relevant_info = []
            for doc, metadata in zip(documents[:2], metadatas[:2]):  # Use top 2 results
                if metadata.get('type') == 'faq':
                    # Extract answer from FAQ
                    answer = metadata.get('answer', '')
                    if answer:
                        relevant_info.append(answer)
                else:
                    # Use document content
                    relevant_info.append(doc)
            
            if not relevant_info:
                return self._generate_fallback_response(user_input, intent, context)
            
            # Choose appropriate template
            templates = self.response_templates.get(intent, self.response_templates['unknown'])
            intro = random.choice(templates)
            
            # Combine intro with retrieved information
            if len(relevant_info) == 1:
                response = f"{intro}\n\n{relevant_info[0]}"
            else:
                response = f"{intro}\n\n{relevant_info[0]}"
                if len(relevant_info) > 1:
                    response += f"\n\nAdditionally: {relevant_info[1]}"
            
            # Add follow-up if appropriate
            follow_up = self._generate_follow_up(intent, context)
            if follow_up:
                response += f"\n\n{follow_up}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating informed response: {e}")
            return self._generate_fallback_response(user_input, intent, context)
    
    def _generate_fallback_response(self, user_input: str, intent: str, context: Dict) -> str:
        """Generate fallback response when no specific information is available"""
        try:
            if intent in self.response_templates:
                base_response = random.choice(self.response_templates[intent])
            else:
                base_response = random.choice(self.response_templates['unknown'])
            
            # Add contextual information if available
            if intent == 'greeting':
                return base_response
            elif intent == 'goodbye':
                return base_response
            elif intent == 'unknown':
                # Try to provide helpful guidance
                return (f"{base_response} "
                       f"I can help you with information about admission requirements, deadlines, "
                       f"tuition fees, programs, financial aid, and more. "
                       f"You can also contact our admissions office directly for personalized assistance.")
            else:
                # Provide general information with contact details
                return (f"{base_response} "
                       f"For the most current and detailed information, please contact our admissions office at "
                       f"admissions@university.edu or call (555) 123-4567.")
            
        except Exception as e:
            self.logger.error(f"Error generating fallback response: {e}")
            return random.choice(FALLBACK_RESPONSES)
    
    def _generate_follow_up(self, intent: str, context: Dict) -> str:
        """Generate appropriate follow-up questions or suggestions"""
        follow_ups = {
            'admission_requirements': "Would you like to know about application deadlines or required documents?",
            'application_deadline': "Do you need information about required documents or the application process?",
            'tuition_fees': "Would you like to learn about financial aid options or payment plans?",
            'programs_offered': "Are you interested in learning about admission requirements for any specific program?",
            'financial_aid': "Would you like information about scholarship deadlines or application procedures?",
            'contact_info': "Is there anything specific you'd like me to help you with before contacting our office?",
            'campus_visit': "Would you like information about academic programs or student life as well?",
            'housing': "Do you have questions about meal plans or campus facilities?"
        }
        
        return follow_ups.get(intent, "Is there anything else I can help you with regarding admissions?")
    
    def _update_context(self, session_id: str, user_input: str, intent: str):
        """Update conversation context"""
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = {
                'inputs': [],
                'intents': [],
                'responses': [],
                'start_time': datetime.now(),
                'last_activity': datetime.now()
            }
        
        context = self.conversation_contexts[session_id]
        context['inputs'].append(user_input)
        context['intents'].append(intent)
        context['last_activity'] = datetime.now()
        
        # Keep only last 10 exchanges to manage memory
        if len(context['inputs']) > 10:
            for key in ['inputs', 'intents', 'responses']:
                context[key] = context[key][-10:]
    
    def _get_context(self, session_id: str) -> Dict:
        """Get conversation context"""
        return self.conversation_contexts.get(session_id, {
            'inputs': [],
            'intents': [],
            'responses': [],
            'start_time': datetime.now(),
            'last_activity': datetime.now()
        })
    
    def _post_process_response(self, response: str, intent: str) -> str:
        """Post-process generated response"""
        try:
            # Clean up response
            response = response.strip()
            
            # Remove any model artifacts
            response = re.sub(r'<\|.*?\|>', '', response)
            response = re.sub(r'\[.*?\]', '', response)
            
            # Ensure proper capitalization
            if response and not response[0].isupper():
                response = response[0].upper() + response[1:]
            
            # Ensure proper ending punctuation
            if response and response[-1] not in '.!?':
                response += '.'
            
            # Limit length
            max_length = 500
            if len(response) > max_length:
                response = response[:max_length].rsplit(' ', 1)[0] + '...'
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error post-processing response: {e}")
            return response
    
    def get_conversation_summary(self, session_id: str) -> Dict:
        """Get summary of conversation"""
        context = self._get_context(session_id)
        
        if not context['inputs']:
            return {'summary': 'No conversation yet', 'topics': [], 'duration': 0}
        
        # Analyze conversation topics
        topics = list(set(context['intents']))
        topics = [topic for topic in topics if topic != 'unknown']
        
        # Calculate duration
        duration = (context['last_activity'] - context['start_time']).total_seconds()
        
        return {
            'summary': f"Discussed {len(topics)} topics over {len(context['inputs'])} exchanges",
            'topics': topics,
            'duration': duration,
            'total_exchanges': len(context['inputs']),
            'start_time': context['start_time'].isoformat(),
            'last_activity': context['last_activity'].isoformat()
        }
    
    def clear_context(self, session_id: str):
        """Clear conversation context for a session"""
        if session_id in self.conversation_contexts:
            del self.conversation_contexts[session_id]
            self.logger.info(f"Cleared context for session: {session_id}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        if self.generator:
            del self.generator
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.conversation_contexts.clear()
        self.logger.info("Dialogue Agent cleaned up")