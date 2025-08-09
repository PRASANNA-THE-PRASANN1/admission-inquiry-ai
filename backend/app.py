from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import json
from datetime import datetime
import traceback
import logging

# Import your modules
from backend.config import *
from backend.agents.asr_agent import ASRAgent
from backend.agents.nlu_agent import NLUAgent
from backend.agents.retrieval_agent import RetrievalAgent
from backend.agents.dialogue_agent import DialogueAgent
from backend.agents.tts_agent import TTSAgent
from backend.agents.followup_agent import FollowUpAgent
from backend.utils.database import DatabaseManager
from backend.utils.logger import setup_logger

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = setup_logger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
# Allow all origins for debugging
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Initialize agents with error handling for each
try:
    logger.info("Initializing ASR agent...")
    asr_agent = ASRAgent()
    
    logger.info("Initializing NLU agent...")
    nlu_agent = NLUAgent()
    
    logger.info("Initializing Retrieval agent...")
    retrieval_agent = RetrievalAgent()
    
    logger.info("Initializing Dialogue agent...")
    dialogue_agent = DialogueAgent()
    
    logger.info("Initializing TTS agent...")
    tts_agent = TTSAgent()
    
    logger.info("Initializing Followup agent...")
    followup_agent = FollowUpAgent()
    
    logger.info("Initializing Database manager...")
    db_manager = DatabaseManager()
    
    logger.info("All agents initialized successfully")
except Exception as e:
    logger.error(f"Error initializing agents: {e}")
    logger.error(traceback.format_exc())
    raise

@app.route('/')
def index():
    """Root endpoint for testing connectivity"""
    return jsonify({
        'message': 'Admission Assistant API is running',
        'timestamp': datetime.now().isoformat()
    })

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
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

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
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name
        
        try:
            # Check if file has content
            file_size = os.path.getsize(temp_audio_path)
            if file_size == 0:
                return jsonify({'error': 'Audio file is empty'}), 400
            
            # Validate audio file
            valid, validation_msg = asr_agent.validate_audio_file(temp_audio_path)
            if not valid:
                return jsonify({'error': f'Invalid audio: {validation_msg}'}), 400
            
            # Transcribe audio
            transcript_result = asr_agent.transcribe(temp_audio_path)
            
            # Check if transcription succeeded
            if not transcript_result or 'error' in transcript_result:
                error_msg = transcript_result.get('error', 'Unknown transcription error') if transcript_result else 'Transcription failed'
                return jsonify({'error': 'Could not transcribe audio', 'details': error_msg}), 400
            
            transcript_text = transcript_result.get('text', '')
            
            if not transcript_text.strip():
                return jsonify({'error': 'Empty transcription result'}), 400
            
            # Process through NLU
            intent_result = nlu_agent.classify_intent(transcript_text)
            
            # Retrieve relevant information
            retrieved_info = retrieval_agent.retrieve(transcript_text, intent_result)
            
            # Generate response
            response_text = dialogue_agent.generate_response(
                transcript_text, intent_result, retrieved_info, session_id
            )
            
            # Generate audio response
            audio_response_path = tts_agent.synthesize(response_text, session_id)
            
            # Log interaction
            db_manager.log_interaction(
                session_id=session_id,
                user_input=transcript_text,
                intent=intent_result.get('intent', 'unknown'),
                confidence=intent_result.get('confidence', 0.0),
                response=response_text,
                channel='voice'
            )
            
            return jsonify({
                'transcript': transcript_text,
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
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    try:
        logger.debug(f"Serving audio file: {filename}")
        audio_path = UPLOAD_FOLDER / filename
        if audio_path.exists():
            return send_file(audio_path, mimetype='audio/wav')
        else:
            logger.error(f"Audio file not found: {audio_path}")
            return jsonify({'error': 'Audio file not found'}), 404
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        return jsonify({'error': 'Error serving audio file', 'details': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request', 'details': str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    logger.error(f"404 error: {request.path}")
    return jsonify({'error': f'Endpoint not found: {request.path}'}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 error: {str(e)}")
    return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting Admission Inquiry Assistant on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)


@app.route('/debug_voice', methods=['POST'])
def debug_voice():
    """Debug endpoint for voice API"""
    try:
        # Log request details
        logger.info(f"Debug voice endpoint called - Headers: {dict(request.headers)}")
        logger.info(f"Request files: {list(request.files.keys())}")
        logger.info(f"Request form: {request.form}")
        
        # Check for audio file
        if 'audio' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No audio file in request',
                'debug_info': {
                    'headers': dict(request.headers),
                    'files': list(request.files.keys()),
                    'form': dict(request.form)
                }
            })
        
        audio_file = request.files['audio']
        
        # Return success without processing
        return jsonify({
            'status': 'success',
            'message': 'Debug endpoint received file successfully',
            'file_info': {
                'filename': audio_file.filename,
                'content_type': audio_file.content_type,
                'content_length': request.headers.get('Content-Length')
            }
        })
    
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        })
    
# Add these error handlers to your app.py file

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 error: {str(e)}")
    error_traceback = traceback.format_exc()
    logger.error(error_traceback)
    return jsonify({
        'error': 'Internal server error',
        'details': str(e),
        'traceback': error_traceback.split('\n')
    }), 500

@app.errorhandler(404)
def not_found(e):
    logger.error(f"404 error: {request.path}")
    return jsonify({
        'error': f'Endpoint not found: {request.path}',
        'details': str(e)
    }), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        'error': 'Bad request',
        'details': str(e)
    }), 400

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'error': 'File too large',
        'details': str(e)
    }), 413