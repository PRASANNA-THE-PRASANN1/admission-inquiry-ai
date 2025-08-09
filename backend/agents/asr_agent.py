import whisper
import torch
import librosa
import soundfile as sf
import os
import tempfile
from pathlib import Path
import logging
import subprocess
import numpy as np

from ..config import WHISPER_MODEL, AUDIO_SAMPLE_RATE

class ASRAgent:
    """Automatic Speech Recognition Agent using OpenAI Whisper"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        
        # Check if ffmpeg is available
        self.ffmpeg_available = self._check_ffmpeg()
        if not self.ffmpeg_available:
            self.logger.warning("FFmpeg not found. WebM audio conversion may fail.")
        
        self.load_model()
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
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
            # Check file extension
            file_ext = os.path.splitext(audio_path)[1].lower()
            self.logger.info(f"Preprocessing audio file with extension: {file_ext}")
            
            temp_wav_path = None
            
            # For webm files, convert to wav using ffmpeg if available
            if file_ext == '.webm':
                if self.ffmpeg_available:
                    # Create a temporary wav file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                        temp_wav_path = temp_wav.name
                    
                    self.logger.info(f"Converting webm to wav using ffmpeg: {audio_path} -> {temp_wav_path}")
                    try:
                        # Run ffmpeg to convert webm to wav
                        cmd = ['ffmpeg', '-i', audio_path, '-ar', str(AUDIO_SAMPLE_RATE), '-ac', '1', '-y', temp_wav_path]
                        self.logger.debug(f"Running command: {' '.join(cmd)}")
                        
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode != 0:
                            self.logger.warning(f"FFmpeg conversion failed: {result.stderr}")
                            raise Exception(f"FFmpeg conversion failed: {result.stderr}")
                        
                        # Check if the converted file exists and has size
                        if os.path.exists(temp_wav_path) and os.path.getsize(temp_wav_path) > 0:
                            self.logger.info(f"Successfully converted webm to wav: {temp_wav_path}")
                            audio_path = temp_wav_path
                        else:
                            self.logger.warning(f"FFmpeg conversion produced empty file")
                            raise Exception("FFmpeg conversion produced empty file")
                            
                    except Exception as e:
                        self.logger.warning(f"Error during ffmpeg conversion: {e}")
                        # Don't use librosa as fallback - it often fails with WebM
                        raise
            
            # Load audio file with librosa
            self.logger.info(f"Loading audio from {audio_path} with librosa")
            audio, sr = librosa.load(audio_path, sr=AUDIO_SAMPLE_RATE)
            
            # Check if audio has content
            if len(audio) == 0 or np.all(np.abs(audio) < 1e-4):
                self.logger.warning("Loaded audio is empty or silent")
                raise Exception("Audio file is empty or silent")
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            self.logger.info(f"Normalized audio: length={len(audio)}, min={audio.min()}, max={audio.max()}")
            
            # Save preprocessed audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, audio, AUDIO_SAMPLE_RATE)
                self.logger.info(f"Saved preprocessed audio to {temp_file.name}")
                return temp_file.name
                
        except Exception as e:
            self.logger.error(f"Error preprocessing audio: {e}")
            raise
        finally:
            # Clean up temp wav file if it exists
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                    self.logger.debug(f"Cleaned up temporary WAV file: {temp_wav_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up temporary WAV file: {e}")
    
    def transcribe(self, audio_path, language='en'):
        """Transcribe audio file to text"""
        try:
            if not os.path.exists(audio_path):
                error_msg = f"Audio file not found: {audio_path}"
                self.logger.error(error_msg)
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language': language,
                    'segments': [],
                    'error': error_msg
                }
            
            # Get file size and details for logging
            file_size = os.path.getsize(audio_path)
            self.logger.info(f"Transcribing audio: {audio_path} (size: {file_size} bytes)")
            
            if file_size == 0:
                error_msg = "Audio file is empty"
                self.logger.error(error_msg)
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language': language,
                    'segments': [],
                    'error': error_msg
                }
            
            # Preprocess audio
            try:
                processed_audio_path = self.preprocess_audio(audio_path)
            except Exception as e:
                error_msg = f"Audio preprocessing failed: {str(e)}"
                self.logger.error(error_msg)
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language': language,
                    'segments': [],
                    'error': error_msg
                }
            
            try:
                # Transcribe using Whisper
                self.logger.info(f"Starting Whisper transcription on {processed_audio_path}")
                
                # Check if the processed file exists and has size
                if not os.path.exists(processed_audio_path) or os.path.getsize(processed_audio_path) == 0:
                    error_msg = "Processed audio file is empty or missing"
                    self.logger.error(error_msg)
                    return {
                        'text': '',
                        'confidence': 0.0,
                        'language': language,
                        'segments': [],
                        'error': error_msg
                    }
                
                # Set Whisper options
                whisper_options = {
                    'language': language,
                    'task': "transcribe",
                    'fp16': False,  # Use fp32 for better compatibility
                    'verbose': True  # Enable verbose output for debugging
                }
                
                # Actually transcribe the audio
                result = self.model.transcribe(
                    processed_audio_path,
                    **whisper_options
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
                    try:
                        os.unlink(processed_audio_path)
                        self.logger.debug(f"Cleaned up temporary file: {processed_audio_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up temporary file: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")
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
            
            # Get file extension
            file_ext = os.path.splitext(audio_path)[1].lower()
            
            # For WebM files, check if ffmpeg is available
            if file_ext == '.webm':
                if not self.ffmpeg_available:
                    return False, "FFmpeg is required for WebM files but not found"
                
                # Check if it's a valid WebM file using ffprobe
                try:
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', audio_path],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        return False, f"Invalid WebM file: {result.stderr}"
                    
                    return True, "Valid WebM audio file"
                except Exception as e:
                    return False, f"Error validating WebM file: {str(e)}"
            
            # For other files, try to load a small sample with librosa
            try:
                audio, sr = librosa.load(audio_path, duration=1, sr=None)
                if len(audio) == 0:
                    return False, "No audio data found"
                return True, "Valid audio file"
            except Exception as e:
                return False, f"Invalid audio format: {str(e)}"
            
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