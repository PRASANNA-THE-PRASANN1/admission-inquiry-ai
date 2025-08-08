import whisper
import torch
import librosa
import soundfile as sf
import os
import tempfile
from pathlib import Path
import logging

from ..config import WHISPER_MODEL, AUDIO_SAMPLE_RATE

class ASRAgent:
    """Automatic Speech Recognition Agent using OpenAI Whisper"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load Whisper model"""
        try:
            self.logger.info(f"Loading Whisper model '{WHISPER_MODEL}' on {self.device}")
            self.model = whisper.load_model(WHISPER_MODEL, device=self.device)
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def preprocess_audio(self, audio_path):
        """Preprocess audio file for Whisper"""
        try:
            # Load audio file
            audio, sr = librosa.load(audio_path, sr=AUDIO_SAMPLE_RATE)
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            # Save preprocessed audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, audio, AUDIO_SAMPLE_RATE)
                return temp_file.name
                
        except Exception as e:
            self.logger.error(f"Error preprocessing audio: {e}")
            raise
    
    def transcribe(self, audio_path, language='en'):
        """Transcribe audio file to text"""
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Preprocess audio
            processed_audio_path = self.preprocess_audio(audio_path)
            
            try:
                # Transcribe using Whisper
                self.logger.info(f"Transcribing audio: {audio_path}")
                result = self.model.transcribe(
                    processed_audio_path,
                    language=language,
                    task="transcribe",
                    fp16=False,  # Use fp32 for better compatibility
                    verbose=False
                )
                
                transcript = result["text"].strip()
                confidence = self._calculate_confidence(result)
                
                self.logger.info(f"Transcription completed. Confidence: {confidence:.2f}")
                self.logger.debug(f"Transcript: {transcript}")
                
                return {
                    'text': transcript,
                    'confidence': confidence,
                    'language': result.get('language', language),
                    'segments': result.get('segments', [])
                }
                
            finally:
                # Clean up preprocessed file
                if os.path.exists(processed_audio_path):
                    os.unlink(processed_audio_path)
                    
        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'language': language,
                'segments': [],
                'error': str(e)
            }
    
    def transcribe_streaming(self, audio_chunks, language='en'):
        """Transcribe streaming audio chunks (for real-time processing)"""
        try:
            # Combine chunks into a single audio file
            combined_audio = []
            for chunk in audio_chunks:
                if isinstance(chunk, bytes):
                    # Convert bytes to numpy array
                    audio_data = librosa.util.buf_to_float(chunk)
                    combined_audio.extend(audio_data)
                else:
                    combined_audio.extend(chunk)
            
            # Save combined audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, combined_audio, AUDIO_SAMPLE_RATE)
                temp_path = temp_file.name
            
            try:
                # Transcribe combined audio
                result = self.transcribe(temp_path, language)
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            self.logger.error(f"Error in streaming transcription: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'language': language,
                'segments': [],
                'error': str(e)
            }
    
    def _calculate_confidence(self, whisper_result):
        """Calculate confidence score from Whisper result"""
        try:
            if 'segments' in whisper_result and whisper_result['segments']:
                # Average confidence from all segments
                confidences = []
                for segment in whisper_result['segments']:
                    if 'avg_logprob' in segment:
                        # Convert log probability to confidence (0-1)
                        confidence = min(1.0, max(0.0, (segment['avg_logprob'] + 1.0)))
                        confidences.append(confidence)
                
                if confidences:
                    return sum(confidences) / len(confidences)
            
            # Fallback confidence calculation
            text_length = len(whisper_result.get('text', '').strip())
            if text_length > 0:
                return min(0.9, 0.5 + (text_length / 100))  # Simple heuristic
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Error calculating confidence: {e}")
            return 0.5  # Default confidence
    
    def validate_audio_file(self, audio_path):
        """Validate audio file format and content"""
        try:
            if not os.path.exists(audio_path):
                return False, "File does not exist"
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                return False, "File is empty"
            
            if file_size > 25 * 1024 * 1024:  # 25MB limit
                return False, "File too large (max 25MB)"
            
            # Try to load audio
            try:
                audio, sr = librosa.load(audio_path, duration=1)  # Load first second
                if len(audio) == 0:
                    return False, "No audio data found"
            except Exception as e:
                return False, f"Invalid audio format: {str(e)}"
            
            return True, "Valid audio file"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_audio_info(self, audio_path):
        """Get audio file information"""
        try:
            audio, sr = librosa.load(audio_path, sr=None)
            duration = len(audio) / sr
            
            return {
                'duration': duration,
                'sample_rate': sr,
                'channels': 1 if audio.ndim == 1 else audio.shape[0],
                'file_size': os.path.getsize(audio_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting audio info: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.model:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        self.logger.info("ASR Agent cleaned up")