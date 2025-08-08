import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading

from ..config import DATABASE_PATH

class DatabaseManager:
    """SQLite Database Manager for storing interactions and analytics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_path = DATABASE_PATH
        self.lock = threading.Lock()  # Thread safety
        
        # Initialize database
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize database with required tables"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Create interactions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        user_input TEXT NOT NULL,
                        intent TEXT,
                        confidence REAL,
                        response TEXT NOT NULL,
                        channel TEXT DEFAULT 'chat',
                        entities TEXT,
                        processing_time REAL,
                        user_satisfaction INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        end_time DATETIME,
                        total_interactions INTEGER DEFAULT 0,
                        user_info TEXT,
                        status TEXT DEFAULT 'active',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create analytics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        additional_data TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date, metric_name)
                    )
                ''')
                
                # Create user feedback table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        interaction_id INTEGER,
                        feedback_type TEXT NOT NULL,
                        rating INTEGER,
                        comments TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (interaction_id) REFERENCES interactions (id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_session ON interactions(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_intent ON interactions(intent)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time)')
                
                conn.commit()
                conn.close()
                
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def log_interaction(self, session_id: str, user_input: str, intent: str, 
                       confidence: float, response: str, channel: str = 'chat',
                       entities: Dict = None, processing_time: float = None) -> int:
        """Log a user interaction"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Convert entities to JSON string
                entities_json = json.dumps(entities) if entities else None
                
                cursor.execute('''
                    INSERT INTO interactions 
                    (session_id, user_input, intent, confidence, response, channel, 
                     entities, processing_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, user_input, intent, confidence, response, 
                      channel, entities_json, processing_time))
                
                interaction_id = cursor.lastrowid
                
                # Update or create session
                cursor.execute('''
                    INSERT OR REPLACE INTO sessions 
                    (session_id, start_time, total_interactions, updated_at)
                    VALUES (?, 
                            COALESCE((SELECT start_time FROM sessions WHERE session_id = ?), CURRENT_TIMESTAMP),
                            COALESCE((SELECT total_interactions FROM sessions WHERE session_id = ?), 0) + 1,
                            CURRENT_TIMESTAMP)
                ''', (session_id, session_id, session_id))
                
                conn.commit()
                conn.close()
                
                self.logger.debug(f"Logged interaction {interaction_id} for session {session_id}")
                return interaction_id
                
        except Exception as e:
            self.logger.error(f"Error logging interaction: {e}")
            return -1
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a session"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, user_input, intent, confidence, 
                           response, channel, entities, processing_time
                    FROM interactions 
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                ''', (session_id, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                history = []
                for row in rows:
                    entities = json.loads(row[7]) if row[7] else {}
                    history.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'user_input': row[2],
                        'intent': row[3],
                        'confidence': row[4],
                        'response': row[5],
                        'channel': row[6],
                        'entities': entities,
                        'processing_time': row[8]
                    })
                
                return history
                
        except Exception as e:
            self.logger.error(f"Error getting session history: {e}")
            return []
    
    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics data for the specified number of days"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                analytics = {}
                
                # Total interactions
                cursor.execute('''
                    SELECT COUNT(*) FROM interactions 
                    WHERE timestamp >= ? AND timestamp <= ?
                ''', (start_date, end_date))
                analytics['total_interactions'] = cursor.fetchone()[0]
                
                # Unique sessions
                cursor.execute('''
                    SELECT COUNT(DISTINCT session_id) FROM interactions 
                    WHERE timestamp >= ? AND timestamp <= ?
                ''', (start_date, end_date))
                analytics['unique_sessions'] = cursor.fetchone()[0]
                
                # Intent distribution
                cursor.execute('''
                    SELECT intent, COUNT(*) as count FROM interactions 
                    WHERE timestamp >= ? AND timestamp <= ? AND intent IS NOT NULL
                    GROUP BY intent
                    ORDER BY count DESC
                ''', (start_date, end_date))
                intent_data = cursor.fetchall()
                analytics['intent_distribution'] = {intent: count for intent, count in intent_data}
                
                # Channel distribution
                cursor.execute('''
                    SELECT channel, COUNT(*) as count FROM interactions 
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY channel
                ''', (start_date, end_date))
                channel_data = cursor.fetchall()
                analytics['channel_distribution'] = {channel: count for channel, count in channel_data}
                
                # Daily interaction counts
                cursor.execute('''
                    SELECT DATE(timestamp) as date, COUNT(*) as count 
                    FROM interactions 
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (start_date, end_date))
                daily_data = cursor.fetchall()
                analytics['daily_interactions'] = {date: count for date, count in daily_data}
                
                # Average confidence by intent
                cursor.execute('''
                    SELECT intent, AVG(confidence) as avg_confidence
                    FROM interactions 
                    WHERE timestamp >= ? AND timestamp <= ? AND confidence IS NOT NULL
                    GROUP BY intent
                ''', (start_date, end_date))
                confidence_data = cursor.fetchall()
                analytics['average_confidence'] = {intent: round(conf, 3) for intent, conf in confidence_data}
                
                # Average processing time
                cursor.execute('''
                    SELECT AVG(processing_time) FROM interactions 
                    WHERE timestamp >= ? AND timestamp <= ? AND processing_time IS NOT NULL
                ''', (start_date, end_date))
                avg_processing_time = cursor.fetchone()[0]
                analytics['average_processing_time'] = round(avg_processing_time, 3) if avg_processing_time else 0
                
                # Most common entities
                cursor.execute('''
                    SELECT entities FROM interactions 
                    WHERE timestamp >= ? AND timestamp <= ? AND entities IS NOT NULL
                ''', (start_date, end_date))
                entities_data = cursor.fetchall()
                
                entity_counts = {}
                for (entities_json,) in entities_data:
                    try:
                        entities = json.loads(entities_json)
                        for entity_type, values in entities.items():
                            if entity_type not in entity_counts:
                                entity_counts[entity_type] = 0
                            entity_counts[entity_type] += len(values) if isinstance(values, list) else 1
                    except:
                        continue
                
                analytics['entity_distribution'] = entity_counts
                
                conn.close()
                
                return analytics
                
        except Exception as e:
            self.logger.error(f"Error getting analytics: {e}")
            return {}
    
    def save_user_feedback(self, session_id: str, feedback_type: str, 
                          rating: int = None, comments: str = None, 
                          interaction_id: int = None) -> bool:
        """Save user feedback"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO user_feedback 
                    (session_id, interaction_id, feedback_type, rating, comments)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, interaction_id, feedback_type, rating, comments))
                
                conn.commit()
                conn.close()
                
                self.logger.info(f"Saved user feedback for session {session_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving user feedback: {e}")
            return False
    
    def get_popular_queries(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Get most popular user queries"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                start_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    SELECT user_input, COUNT(*) as frequency, 
                           AVG(confidence) as avg_confidence
                    FROM interactions 
                    WHERE timestamp >= ? AND LENGTH(user_input) > 5
                    GROUP BY LOWER(TRIM(user_input))
                    ORDER BY frequency DESC
                    LIMIT ?
                ''', (start_date, limit))
                
                results = cursor.fetchall()
                conn.close()
                
                popular_queries = []
                for query, frequency, avg_confidence in results:
                    popular_queries.append({
                        'query': query,
                        'frequency': frequency,
                        'avg_confidence': round(avg_confidence, 3) if avg_confidence else 0
                    })
                
                return popular_queries
                
        except Exception as e:
            self.logger.error(f"Error getting popular queries: {e}")
            return []
    
    def get_low_confidence_interactions(self, threshold: float = 0.5, limit: int = 50) -> List[Dict]:
        """Get interactions with low confidence scores for improvement"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, session_id, user_input, intent, 
                           confidence, response
                    FROM interactions 
                    WHERE confidence < ? AND confidence IS NOT NULL
                    ORDER BY confidence ASC
                    LIMIT ?
                ''', (threshold, limit))
                
                results = cursor.fetchall()
                conn.close()
                
                low_confidence = []
                for row in results:
                    low_confidence.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'session_id': row[2],
                        'user_input': row[3],
                        'intent': row[4],
                        'confidence': row[5],
                        'response': row[6]
                    })
                
                return low_confidence
                
        except Exception as e:
            self.logger.error(f"Error getting low confidence interactions: {e}")
            return []
    
    def update_session_status(self, session_id: str, status: str, user_info: Dict = None):
        """Update session status and user information"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                user_info_json = json.dumps(user_info) if user_info else None
                
                cursor.execute('''
                    UPDATE sessions 
                    SET status = ?, user_info = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                ''', (status, user_info_json, session_id))
                
                if status == 'ended':
                    cursor.execute('''
                        UPDATE sessions 
                        SET end_time = CURRENT_TIMESTAMP
                        WHERE session_id = ?
                    ''', (session_id,))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error updating session status: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to manage database size"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                # Delete old interactions
                cursor.execute('DELETE FROM interactions WHERE timestamp < ?', (cutoff_date,))
                interactions_deleted = cursor.rowcount
                
                # Delete orphaned sessions
                cursor.execute('''
                    DELETE FROM sessions 
                    WHERE session_id NOT IN (SELECT DISTINCT session_id FROM interactions)
                ''')
                sessions_deleted = cursor.rowcount
                
                # Delete old analytics
                cursor.execute('DELETE FROM analytics WHERE created_at < ?', (cutoff_date,))
                analytics_deleted = cursor.rowcount
                
                # Delete old feedback
                cursor.execute('DELETE FROM user_feedback WHERE created_at < ?', (cutoff_date,))
                feedback_deleted = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                self.logger.info(f"Cleanup completed: {interactions_deleted} interactions, "
                               f"{sessions_deleted} sessions, {analytics_deleted} analytics, "
                               f"{feedback_deleted} feedback records deleted")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                stats = {}
                
                # Table counts
                tables = ['interactions', 'sessions', 'analytics', 'user_feedback']
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[f'{table}_count'] = cursor.fetchone()[0]
                
                # Database size
                stats['database_size_mb'] = round(Path(self.db_path).stat().st_size / (1024 * 1024), 2)
                
                # Date range of data
                cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM interactions')
                date_range = cursor.fetchone()
                if date_range[0]:
                    stats['data_date_range'] = {
                        'start': date_range[0],
                        'end': date_range[1]
                    }
                
                conn.close()
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close(self):
        """Close database connections (cleanup method)"""
        # SQLite connections are closed after each operation
        self.logger.info("Database manager closed")