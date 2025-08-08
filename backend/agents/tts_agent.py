import logging
import os
import tempfile
from pathlib import Path
import re
from datetime import datetime
import torch
import soundfile as sf

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logging.warning("TTS library not available. Text-to-speech functionality will be limited.")

from ..config import TTS_MODEL, UPLOAD_FOLDER, AUDIO_SAMPLE_RATE

class TTSAgent:
    """Text-to-Speech Agent using Coqui TTS"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts_model = None
        self.audio_output_dir = UPLOAD_FOLDER
        
        # Ensure output directory exists
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize TTS model
        if TTS_AVAILABLE:
            self.load_model()
        else:
            self.logger.warning("TTS functionality disabled - library not available")
    
    def load_model(self):
        """Load TTS model"""
        try:
            if not TTS_AVAILABLE:
                self.logger.error("TTS library not available")
                return
            
            self.logger.info(f"Loading TTS model on {self.device}")
            
            # Use a lightweight English TTS model
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"
            
            try:
                self.tts_model = TTS(model_name=model_name).to(self.device)
                self.logger.info(f"TTS model '{model_name}' loaded successfully")
            except Exception as e:
                self.logger.warning(f"Failed to load {model_name}, trying fallback model")
                # Fallback to a more basic model
                try:
                    self.tts_model = TTS(model_name="tts_models/en/ljspeech/glow-tts").to(self.device)
                    self.logger.info("Fallback TTS model loaded successfully")
                except Exception as e2:
                    self.logger.error(f"Failed to load fallback TTS model: {e2}")
                    self.tts_model = None
                
        except Exception as e:
            self.logger.error(f"Error loading TTS model: {e}")
            self.tts_model = None
    
    def synthesize(self, text: str, session_id: str = "default", speaker: str = None) -> str:
        """Synthesize text to speech and return audio file path"""
        try:
            if not TTS_AVAILABLE or not self.tts_model:
                return self._create_silent_audio(session_id)
            
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            if not processed_text.strip():
                return self._create_silent_audio(session_id)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{session_id}_{timestamp}.wav"
            output_path = self.audio_output_dir / filename
            
            self.logger.info(f"Synthesizing text: {processed_text[:50]}...")
            
            # Generate speech
            self.tts_model.tts_to_file(
                text=processed_text,
                file_path=str(output_path)
            )
            
            # Verify audio file was created
            if output_path.exists() and output_path.stat().st_size > 0:
                self.logger.info(f"Audio synthesized successfully: {filename}")
                return str(output_path)
            else:
                self.logger.error("TTS failed to generate audio file")
                return self._create_silent_audio(session_id)
                
        except Exception as e:
            self.logger.error(f"Error synthesizing speech: {e}")
            return self._create_silent_audio(session_id)
    
    def synthesize_streaming(self, text_chunks: list, session_id: str = "default") -> list:
        """Synthesize multiple text chunks for streaming"""
        audio_files = []
        
        try:
            for i, chunk in enumerate(text_chunks):
                if chunk.strip():
                    chunk_session_id = f"{session_id}_chunk_{i}"
                    audio_file = self.synthesize(chunk, chunk_session_id)
                    if audio_file:
                        audio_files.append(audio_file)
            
            return audio_files
            
        except Exception as e:
            self.logger.error(f"Error in streaming synthesis: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better TTS output"""
        try:
            # Remove markdown formatting
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
            text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
            text = re.sub(r'`(.*?)`', r'\1', text)        # Code
            
            # Remove URLs
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 'link', text)
            
            # Replace email addresses
            text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email address', text)
            
            # Replace phone numbers
            text = re.sub(r'\b\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b', r'\1 \2 \3', text)
            
            # Handle abbreviations
            abbreviations = {
                'Dr.': 'Doctor',
                'Mr.': 'Mister',
                'Mrs.': 'Missus',
                'Ms.': 'Miss',
                'Prof.': 'Professor',
                'vs.': 'versus',
                'etc.': 'etcetera',
                'e.g.': 'for example',
                'i.e.': 'that is',
                'FAQ': 'F A Q',
                'GPA': 'G P A',
                'SAT': 'S A T',
                'ACT': 'A C T',
                'USA': 'U S A',
                'PhD': 'P H D',
                'MBA': 'M B A'
            }
            
            for abbr, expansion in abbreviations.items():
                text = text.replace(abbr, expansion)
            
            # Clean up multiple spaces and newlines
            text = re.sub(r'\n+', '. ', text)
            text = re.sub(r'\s+', ' ', text)
            
            # Limit length (TTS models have token limits)
            max_length = 500
            if len(text) > max_length:
                # Split at sentence boundary
                sentences = text.split('. ')
                truncated = ""
                for sentence in sentences:
                    if len(truncated + sentence) < max_length:
                        truncated += sentence + ". "
                    else:
                        break
                text = truncated.strip()
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error preprocessing text: {e}")
            return text
    
    def _create_silent_audio(self, session_id: str, duration: float = 1.0) -> str:
        """Create a silent audio file as fallback"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"silent_{session_id}_{timestamp}.wav"
            output_path = self.audio_output_dir / filename
            
            # Generate silent audio
            import numpy as np
            silent_audio = np.zeros(int(AUDIO_SAMPLE_RATE * duration))
            
            # Save as WAV file
            sf.write(str(output_path), silent_audio, AUDIO_SAMPLE_RATE)
            
            self.logger.info(f"Created silent audio file: {filename}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error creating silent audio: {e}")
            return ""
    
    def convert_text_to_ssml(self, text: str, voice_settings: dict = None) -> str:
        """Convert plain text to SSML for better control"""
        try:
            if voice_settings is None:
                voice_settings = {
                    'rate': 'medium',
                    'pitch': 'medium',
                    'volume': 'medium'
                }
            
            # Basic SSML structure
            ssml = f"""
            <speak>
                <prosody rate="{voice_settings.get('rate', 'medium')}" 
                         pitch="{voice_settings.get('pitch', 'medium')}" 
                         volume="{voice_settings.get('volume', 'medium')}">
                    {text}
                </prosody>
            </speak>
            """
            
            return ssml.strip()
            
        except Exception as e:
            self.logger.error(f"Error converting to SSML: {e}")
            return text
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices"""
        try:
            if not TTS_AVAILABLE:
                return []
            
            # This would depend on the specific TTS model being used
            # For now, return a default list
            return [
                {"name": "default", "language": "en", "gender": "female"},
                {"name": "ljspeech", "language": "en", "gender": "female"}
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting available voices: {e}")
            return []
    
    def validate_text(self, text: str) -> tuple:
        """Validate text for TTS synthesis"""
        try:
            if not text or not text.strip():
                return False, "Text is empty"
            
            if len(text) > 1000:
                return False, "Text too long (max 1000 characters)"
            
            # Check for unsupported characters
            unsupported_chars = re.findall(r'[^\w\s\.,!?;:\-\(\)\'\"@#$%&*+/=<>]', text)
            if unsupported_chars:
                return False, f"Unsupported characters found: {set(unsupported_chars)}"
            
            return True, "Text is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old audio files"""
        try:
            current_time = datetime.now()
            deleted_count = 0
            
            for audio_file in self.audio_output_dir.glob("*.wav"):
                try:
                    file_time = datetime.fromtimestamp(audio_file.stat().st_mtime)
                    age_hours = (current_time - file_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        audio_file.unlink()
                        deleted_count += 1
                        
                except Exception as e:
                    self.logger.warning(f"Error processing file {audio_file}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old audio files")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up audio files: {e}")
    
    def get_audio_info(self, audio_path: str) -> dict:
        """Get information about generated audio file"""
        try:
            if not os.path.exists(audio_path):
                return {}
            
            # Read audio file info
            import librosa
            audio, sr = librosa.load(audio_path, sr=None)
            duration = len(audio) / sr
            
            return {
                'duration': duration,
                'sample_rate': sr,
                'channels': 1 if audio.ndim == 1 else audio.shape[0],
                'file_size': os.path.getsize(audio_path),
                'format': 'wav'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting audio info: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.tts_model:
            del self.tts_model
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Clean up recent audio files
        self.cleanup_old_files(max_age_hours=1)
        
        self.logger.info("TTS Agent cleaned up")