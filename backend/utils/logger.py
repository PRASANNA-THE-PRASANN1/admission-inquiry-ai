import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import colorlog

from ..config import LOG_LEVEL, LOG_FILE

def setup_logger(name: str = None, level: str = None, log_to_file: bool = True, 
                log_to_console: bool = True) -> logging.Logger:
    """Setup and configure logger with both file and console handlers"""
    
    # Create logger
    logger_name = name or 'admission_assistant'
    logger = logging.getLogger(logger_name)
    
    # Set log level
    log_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # File handler with rotation
    if log_to_file and LOG_FILE:
        try:
            # Ensure log directory exists
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                LOG_FILE,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Error handler for critical errors
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE.parent / 'errors.log' if LOG_FILE else Path('logs/errors.log'),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger

def setup_component_logger(component_name: str, parent_logger: str = 'admission_assistant') -> logging.Logger:
    """Setup logger for specific component"""
    logger_name = f"{parent_logger}.{component_name}"
    return logging.getLogger(logger_name)

def log_performance(logger: logging.Logger, operation: str, start_time: datetime, 
                   end_time: datetime = None, additional_info: dict = None):
    """Log performance metrics for operations"""
    if end_time is None:
        end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    
    log_message = f"Performance - {operation}: {duration:.3f}s"
    
    if additional_info:
        info_str = ", ".join([f"{k}={v}" for k, v in additional_info.items()])
        log_message += f" ({info_str})"
    
    if duration > 5.0:  # Log as warning if operation takes more than 5 seconds
        logger.warning(log_message)
    else:
        logger.info(log_message)

def log_user_interaction(logger: logging.Logger, session_id: str, user_input: str, 
                        intent: str, confidence: float, response_length: int):
    """Log user interaction details"""
    logger.info(f"User Interaction - Session: {session_id}, "
               f"Intent: {intent} (confidence: {confidence:.3f}), "
               f"Input length: {len(user_input)}, Response length: {response_length}")

def log_error_with_context(logger: logging.Logger, error: Exception, 
                          context: dict = None, user_session: str = None):
    """Log error with additional context information"""
    error_msg = f"Error: {type(error).__name__}: {str(error)}"
    
    if user_session:
        error_msg += f" (Session: {user_session})"
    
    if context:
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        error_msg += f" Context: {context_str}"
    
    logger.error(error_msg, exc_info=True)

def log_system_status(logger: logging.Logger, component: str, status: str, 
                     details: dict = None):
    """Log system component status"""
    status_msg = f"System Status - {component}: {status}"
    
    if details:
        details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
        status_msg += f" ({details_str})"
    
    if status.lower() in ['error', 'failed', 'down']:
        logger.error(status_msg)
    elif status.lower() in ['warning', 'degraded']:
        logger.warning(status_msg)
    else:
        logger.info(status_msg)

class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.additional_info = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        
        if exc_type is not None:
            # Log error if exception occurred
            self.logger.error(f"Operation failed: {self.operation} - {exc_type.__name__}: {exc_val}")
        else:
            # Log successful completion
            log_performance(self.logger, self.operation, self.start_time, end_time, self.additional_info)

class StructuredLogger:
    """Structured logging helper for JSON-like log entries"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_event(self, event_type: str, level: str = 'INFO', **kwargs):
        """Log structured event"""
        import json
        
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, json.dumps(log_data, default=str))
    
    def log_user_action(self, session_id: str, action: str, **kwargs):
        """Log user action"""
        self.log_event(
            'user_action',
            session_id=session_id,
            action=action,
            **kwargs
        )
    
    def log_system_event(self, component: str, event: str, **kwargs):
        """Log system event"""
        self.log_event(
            'system_event',
            component=component,
            event=event,
            **kwargs
        )
    
    def log_api_request(self, endpoint: str, method: str, status_code: int, 
                       response_time: float, **kwargs):
        """Log API request"""
        self.log_event(
            'api_request',
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            **kwargs
        )

def setup_request_logging():
    """Setup request logging for Flask app"""
    import flask
    from werkzeug.serving import WSGIRequestHandler
    
    # Custom request handler to log requests
    class RequestHandler(WSGIRequestHandler):
        def log_request(self, code='-', size='-'):
            if code != 200:  # Log non-200 responses
                self.log('info', '"%s" %s %s', self.requestline, code, size)
    
    return RequestHandler

def get_log_stats(log_file_path: Path = None) -> dict:
    """Get statistics about log files"""
    if log_file_path is None:
        log_file_path = LOG_FILE
    
    try:
        if not log_file_path.exists():
            return {'error': 'Log file does not exist'}
        
        # File size
        file_size = log_file_path.stat().st_size
        
        # Line count and log level distribution
        line_count = 0
        level_counts = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        }
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                for level in level_counts.keys():
                    if f" - {level} - " in line:
                        level_counts[level] += 1
                        break
        
        return {
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'total_lines': line_count,
            'level_distribution': level_counts,
            'last_modified': datetime.fromtimestamp(log_file_path.stat().st_mtime).isoformat()
        }
    
    except Exception as e:
        return {'error': f'Error reading log file: {str(e)}'}

def cleanup_old_logs(log_directory: Path = None, days_to_keep: int = 30):
    """Clean up old log files"""
    if log_directory is None:
        log_directory = LOG_FILE.parent if LOG_FILE else Path('logs')
    
    try:
        if not log_directory.exists():
            return
        
        cutoff_time = datetime.now() - Path.timedelta(days=days_to_keep)
        
        deleted_count = 0
        for log_file in log_directory.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time.timestamp():
                log_file.unlink()
                deleted_count += 1
        
        return {'deleted_files': deleted_count}
    
    except Exception as e:
        return {'error': f'Error cleaning up logs: {str(e)}'}

# Convenience function to setup the main application logger
def setup_app_logging():
    """Setup main application logging"""
    logger = setup_logger('admission_assistant')
    logger.info("Admission Assistant logging system initialized")
    return logger