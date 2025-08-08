from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import json
from datetime import datetime
import traceback

from backend.config import *
from backend.agents.asr_agent import ASRAgent
from backend.agents.nlu_agent import NLUAgent
from backend.agents.retrieval_agent import RetrievalAgent
from backend.agents.dialogue_agent import DialogueAgent
from backend.agents.tts_agent import TTSAgent
from backend.agents.followup_agent import FollowUpAgent
from backend.utils.database import DatabaseManager
from backend.utils.logger import setup_logger

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Setup logging
logger = setup_logger()

# Initialize agents
try:
    asr_agent = ASRAgent()
    nlu_agent = NLUAgent()
    retrieval_agent = RetrievalAgent()
    dialogue_agent = DialogueAgent()
    tts_agent = TTSAgent()
    followup_agent = FollowUpAgent()
    db_manager = DatabaseManager()
    
    logger.info("All agents initialized successfully")
except Exception as e:
    logger.error(f"Error initializing agents: {e}")
    raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'agents': {
            'asr': 'initialized',
            'nlu': 'initialized', 
            'retrieval': 'initialized',
            'dialogue': 'initialized',
            'tts': 'initialized',
            'followup': 'initialized'
        }
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Text-based chat endpoint"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Process through NLU
        intent_result = nlu_agent.classify_intent(user_message)
        
        # Retrieve relevant information
        retrieved_info = retrieval_agent.retrieve(user_message, intent_result)
        
        # Generate response
        response = dialogue_agent.generate_response(
            user_message, intent_result, retrieved_info, session_id
        )
        
        # Log interaction
        db_manager.log_interaction(
            session_id=session_id,
            user_input=user_message,
            intent=intent_result.get('intent', 'unknown'),
            confidence=intent_result.get('confidence', 0.0),
            response=response,
            channel='chat'
        )
        
        return jsonify({
            'response': response,
            'intent': intent_result.get('intent'),
            'confidence': intent_result.get('confidence'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/voice', methods=['POST'])
def voice_chat():
    """Voice-based chat endpoint"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', 'default')
        
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save uploaded audio temporarily
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name
        
        try:
            # Transcribe audio
            transcript = asr_agent.transcribe(temp_audio_path)
            
            if not transcript.strip():
                return jsonify({'error': 'Could not transcribe audio'}), 400
            
            # Process through NLU
            intent_result = nlu_agent.classify_intent(transcript)
            
            # Retrieve relevant information
            retrieved_info = retrieval_agent.retrieve(transcript, intent_result)
            
            # Generate response
            response_text = dialogue_agent.generate_response(
                transcript, intent_result, retrieved_info, session_id
            )
            
            # Generate audio response
            audio_response_path = tts_agent.synthesize(response_text, session_id)
            
            # Log interaction
            db_manager.log_interaction(
                session_id=session_id,
                user_input=transcript,
                intent=intent_result.get('intent', 'unknown'),
                confidence=intent_result.get('confidence', 0.0),
                response=response_text,
                channel='voice'
            )
            
            return jsonify({
                'transcript': transcript,
                'response': response_text,
                'audio_url': f'/audio/{os.path.basename(audio_response_path)}',
                'intent': intent_result.get('intent'),
                'confidence': intent_result.get('confidence'),
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
        
    except Exception as e:
        logger.error(f"Error in voice endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    try:
        audio_path = UPLOAD_FOLDER / filename
        if audio_path.exists():
            return send_file(audio_path, mimetype='audio/wav')
        else:
            return jsonify({'error': 'Audio file not found'}), 404
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        return jsonify({'error': 'Error serving audio file'}), 500

@app.route('/followup', methods=['POST'])
def send_followup():
    """Send follow-up email"""
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name', 'Student')
        inquiry_type = data.get('inquiry_type', 'general')
        session_id = data.get('session_id', 'default')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Get conversation history
        history = db_manager.get_session_history(session_id)
        
        # Send follow-up email
        success = followup_agent.send_followup_email(
            email, name, inquiry_type, history
        )
        
        if success:
            return jsonify({
                'message': 'Follow-up email sent successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to send follow-up email'}), 500
            
    except Exception as e:
        logger.error(f"Error in followup endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data"""
    try:
        days = request.args.get('days', 7, type=int)
        
        analytics_data = db_manager.get_analytics(days)
        
        return jsonify({
            'analytics': analytics_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in analytics endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/knowledge', methods=['GET'])
def get_knowledge_base():
    """Get knowledge base entries"""
    try:
        with open(KNOWLEDGE_BASE_PATH, 'r') as f:
            knowledge_base = json.load(f)
        
        return jsonify(knowledge_base)
        
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/knowledge', methods=['POST'])
def update_knowledge_base():
    """Update knowledge base (admin endpoint)"""
    try:
        data = request.get_json()
        
        # Load existing knowledge base
        with open(KNOWLEDGE_BASE_PATH, 'r') as f:
            knowledge_base = json.load(f)
        
        # Update with new data
        if 'faqs' in data:
            knowledge_base['faqs'].extend(data['faqs'])
        
        # Save updated knowledge base
        with open(KNOWLEDGE_BASE_PATH, 'w') as f:
            json.dump(knowledge_base, f, indent=2)
        
        # Reinitialize retrieval agent to update embeddings
        retrieval_agent.initialize_knowledge_base()
        
        return jsonify({
            'message': 'Knowledge base updated successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating knowledge base: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info(f"Starting Admission Inquiry Assistant on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)