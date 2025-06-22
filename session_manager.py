#!/usr/bin/env python3
"""
Session Manager - Transcription history and session management for Dicto

Provides comprehensive session management with transcription history,
metadata storage, and quick access to previous transcriptions.

Features:
- Transcription history with timestamps and metadata
- Session persistence and recovery
- Quick access to recent transcriptions
- Export and import functionality
- Search and filtering capabilities

Dependencies:
- json: Data serialization
- sqlite3: Local database storage
- pathlib: File system operations
"""

import os
import json
import sqlite3
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class SessionStatus(Enum):
    """Session status types."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TranscriptionSession:
    """Transcription session data structure."""
    session_id: str
    timestamp: datetime
    duration: float  # seconds
    audio_file_path: Optional[str]
    transcription_text: str
    confidence_score: Optional[float]
    word_count: int
    character_count: int
    language: str
    model_used: str
    status: SessionStatus
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptionSession':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['status'] = SessionStatus(data['status'])
        return cls(**data)


@dataclass
class SessionStats:
    """Session statistics."""
    total_sessions: int
    successful_sessions: int
    failed_sessions: int
    total_duration: float
    total_words: int
    total_characters: int
    average_confidence: Optional[float]
    most_recent_session: Optional[datetime]
    most_active_day: Optional[str]


class SessionManager:
    """
    SessionManager - Comprehensive transcription history and session management.
    
    Provides persistent storage, search capabilities, and metadata management
    for all transcription sessions.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize SessionManager.
        
        Args:
            storage_dir: Directory for storing session data. Uses default if None.
        """
        self.logger = logging.getLogger(__name__ + ".SessionManager")
        
        # Setup storage directory
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / ".dicto" / "sessions"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Database setup
        self.db_path = self.storage_dir / "sessions.db"
        self.json_backup_path = self.storage_dir / "sessions_backup.json"
        
        # Initialize database
        self._init_database()
        
        # Session cache
        self.session_cache: Dict[str, TranscriptionSession] = {}
        self.cache_limit = 100
        
        self.logger.info(f"SessionManager initialized with storage: {self.storage_dir}")
    
    def _init_database(self):
        """Initialize SQLite database for session storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        duration REAL NOT NULL,
                        audio_file_path TEXT,
                        transcription_text TEXT NOT NULL,
                        confidence_score REAL,
                        word_count INTEGER NOT NULL,
                        character_count INTEGER NOT NULL,
                        language TEXT NOT NULL,
                        model_used TEXT NOT NULL,
                        status TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON sessions(timestamp)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_status ON sessions(status)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at ON sessions(created_at)
                """)
                conn.commit()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_session(self, 
                      transcription_text: str,
                      duration: float,
                      audio_file_path: Optional[str] = None,
                      confidence_score: Optional[float] = None,
                      language: str = "en",
                      model_used: str = "whisper",
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new transcription session.
        
        Args:
            transcription_text: The transcribed text.
            duration: Recording duration in seconds.
            audio_file_path: Path to audio file (optional).
            confidence_score: Transcription confidence (0.0-1.0).
            language: Language code.
            model_used: Model identifier.
            metadata: Additional metadata.
            
        Returns:
            str: Unique session ID.
        """
        try:
            # Generate session ID
            session_id = f"session_{int(time.time() * 1000)}_{len(transcription_text)}"
            
            # Calculate text statistics
            word_count = len(transcription_text.split())
            character_count = len(transcription_text)
            
            # Create session object
            session = TranscriptionSession(
                session_id=session_id,
                timestamp=datetime.now(),
                duration=duration,
                audio_file_path=audio_file_path,
                transcription_text=transcription_text,
                confidence_score=confidence_score,
                word_count=word_count,
                character_count=character_count,
                language=language,
                model_used=model_used,
                status=SessionStatus.COMPLETED,
                metadata=metadata or {}
            )
            
            # Store in database
            self._store_session(session)
            
            # Add to cache
            self.session_cache[session_id] = session
            self._trim_cache()
            
            self.logger.info(f"Created session: {session_id} ({word_count} words)")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise
    
    def _store_session(self, session: TranscriptionSession):
        """Store session in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO sessions (
                        session_id, timestamp, duration, audio_file_path,
                        transcription_text, confidence_score, word_count,
                        character_count, language, model_used, status, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.timestamp.isoformat(),
                    session.duration,
                    session.audio_file_path,
                    session.transcription_text,
                    session.confidence_score,
                    session.word_count,
                    session.character_count,
                    session.language,
                    session.model_used,
                    session.status.value,
                    json.dumps(session.metadata)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[TranscriptionSession]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            TranscriptionSession or None if not found.
        """
        try:
            # Check cache first
            if session_id in self.session_cache:
                return self.session_cache[session_id]
            
            # Query database
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM sessions WHERE session_id = ?
                """, (session_id,))
                row = cursor.fetchone()
                
                if row:
                    session = self._row_to_session(row)
                    self.session_cache[session_id] = session
                    return session
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def get_recent_sessions(self, limit: int = 10) -> List[TranscriptionSession]:
        """
        Get recent transcription sessions.
        
        Args:
            limit: Maximum number of sessions to return.
            
        Returns:
            List of recent sessions ordered by timestamp (newest first).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM sessions 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                sessions = []
                for row in cursor.fetchall():
                    session = self._row_to_session(row)
                    sessions.append(session)
                    # Cache recent sessions
                    self.session_cache[session.session_id] = session
                
                self.logger.info(f"Retrieved {len(sessions)} recent sessions")
                return sessions
                
        except Exception as e:
            self.logger.error(f"Failed to get recent sessions: {e}")
            return []
    
    def search_sessions(self, 
                       query: str,
                       limit: int = 50,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[TranscriptionSession]:
        """
        Search sessions by text content.
        
        Args:
            query: Search query string.
            limit: Maximum results to return.
            start_date: Start date filter (optional).
            end_date: End date filter (optional).
            
        Returns:
            List of matching sessions.
        """
        try:
            sql = """
                SELECT * FROM sessions 
                WHERE transcription_text LIKE ?
            """
            params = [f"%{query}%"]
            
            # Add date filters
            if start_date:
                sql += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                sql += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql, params)
                
                sessions = []
                for row in cursor.fetchall():
                    session = self._row_to_session(row)
                    sessions.append(session)
                
                self.logger.info(f"Search '{query}' returned {len(sessions)} results")
                return sessions
                
        except Exception as e:
            self.logger.error(f"Failed to search sessions: {e}")
            return []
    
    def get_session_stats(self, days: int = 30) -> SessionStats:
        """
        Get session statistics for the specified period.
        
        Args:
            days: Number of days to analyze.
            
        Returns:
            SessionStats object with aggregated statistics.
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_sessions,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_sessions,
                        SUM(duration) as total_duration,
                        SUM(word_count) as total_words,
                        SUM(character_count) as total_characters,
                        AVG(confidence_score) as average_confidence,
                        MAX(timestamp) as most_recent_session
                    FROM sessions 
                    WHERE timestamp >= ?
                """, (start_date.isoformat(),))
                
                row = cursor.fetchone()
                
                # Get most active day
                cursor = conn.execute("""
                    SELECT DATE(timestamp) as day, COUNT(*) as count
                    FROM sessions 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY count DESC
                    LIMIT 1
                """, (start_date.isoformat(),))
                
                most_active_row = cursor.fetchone()
                most_active_day = most_active_row['day'] if most_active_row else None
                
                stats = SessionStats(
                    total_sessions=row['total_sessions'] or 0,
                    successful_sessions=row['successful_sessions'] or 0,
                    failed_sessions=row['failed_sessions'] or 0,
                    total_duration=row['total_duration'] or 0.0,
                    total_words=row['total_words'] or 0,
                    total_characters=row['total_characters'] or 0,
                    average_confidence=row['average_confidence'],
                    most_recent_session=datetime.fromisoformat(row['most_recent_session']) if row['most_recent_session'] else None,
                    most_active_day=most_active_day
                )
                
                self.logger.info(f"Generated stats for {days} days: {stats.total_sessions} sessions")
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get session stats: {e}")
            return SessionStats(0, 0, 0, 0.0, 0, 0, None, None, None)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session to delete.
            
        Returns:
            bool: True if deleted successfully.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM sessions WHERE session_id = ?
                """, (session_id,))
                conn.commit()
                
                # Remove from cache
                self.session_cache.pop(session_id, None)
                
                deleted = cursor.rowcount > 0
                if deleted:
                    self.logger.info(f"Deleted session: {session_id}")
                else:
                    self.logger.warning(f"Session not found for deletion: {session_id}")
                
                return deleted
                
        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def export_sessions(self, 
                       output_path: str,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       format: str = "json") -> bool:
        """
        Export sessions to file.
        
        Args:
            output_path: Output file path.
            start_date: Start date filter (optional).
            end_date: End date filter (optional).
            format: Export format ("json" or "csv").
            
        Returns:
            bool: True if exported successfully.
        """
        try:
            # Get sessions to export
            sql = "SELECT * FROM sessions"
            params = []
            
            if start_date or end_date:
                conditions = []
                if start_date:
                    conditions.append("timestamp >= ?")
                    params.append(start_date.isoformat())
                if end_date:
                    conditions.append("timestamp <= ?")
                    params.append(end_date.isoformat())
                sql += " WHERE " + " AND ".join(conditions)
            
            sql += " ORDER BY timestamp DESC"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql, params)
                
                sessions = []
                for row in cursor.fetchall():
                    session = self._row_to_session(row)
                    sessions.append(session.to_dict())
                
                # Export based on format
                if format.lower() == "json":
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(sessions, f, indent=2, ensure_ascii=False)
                elif format.lower() == "csv":
                    import csv
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        if sessions:
                            writer = csv.DictWriter(f, fieldnames=sessions[0].keys())
                            writer.writeheader()
                            writer.writerows(sessions)
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                self.logger.info(f"Exported {len(sessions)} sessions to {output_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to export sessions: {e}")
            return False
    
    def backup_sessions(self) -> bool:
        """
        Create backup of all sessions.
        
        Returns:
            bool: True if backup created successfully.
        """
        try:
            return self.export_sessions(str(self.json_backup_path), format="json")
        except Exception as e:
            self.logger.error(f"Failed to backup sessions: {e}")
            return False
    
    def cleanup_old_sessions(self, days: int = 90) -> int:
        """
        Clean up sessions older than specified days.
        
        Args:
            days: Age threshold in days.
            
        Returns:
            int: Number of sessions deleted.
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM sessions WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                conn.commit()
                
                deleted_count = cursor.rowcount
                
                # Clear relevant cache entries
                to_remove = []
                for session_id, session in self.session_cache.items():
                    if session.timestamp < cutoff_date:
                        to_remove.append(session_id)
                
                for session_id in to_remove:
                    del self.session_cache[session_id]
                
                self.logger.info(f"Cleaned up {deleted_count} old sessions (older than {days} days)")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
    
    def _row_to_session(self, row: sqlite3.Row) -> TranscriptionSession:
        """Convert database row to TranscriptionSession."""
        return TranscriptionSession(
            session_id=row['session_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            duration=row['duration'],
            audio_file_path=row['audio_file_path'],
            transcription_text=row['transcription_text'],
            confidence_score=row['confidence_score'],
            word_count=row['word_count'],
            character_count=row['character_count'],
            language=row['language'],
            model_used=row['model_used'],
            status=SessionStatus(row['status']),
            metadata=json.loads(row['metadata'] or '{}')
        )
    
    def _trim_cache(self):
        """Trim cache to limit size."""
        if len(self.session_cache) > self.cache_limit:
            # Remove oldest entries
            items = list(self.session_cache.items())
            items.sort(key=lambda x: x[1].timestamp)
            
            to_remove = items[:len(items) - self.cache_limit]
            for session_id, _ in to_remove:
                del self.session_cache[session_id]
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information and statistics."""
        try:
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sessions")
                total_sessions = cursor.fetchone()[0]
            
            return {
                "storage_dir": str(self.storage_dir),
                "database_path": str(self.db_path),
                "database_size": db_size,
                "total_sessions": total_sessions,
                "cache_size": len(self.session_cache),
                "cache_limit": self.cache_limit
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage info: {e}")
            return {}
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            # Check if backup_sessions method still exists and object is properly initialized
            if hasattr(self, 'backup_sessions') and hasattr(self, 'json_backup_path'):
                self.backup_sessions()
        except (NameError, AttributeError, TypeError):
            # Handle cases where builtins like 'open' are not available during destruction
            pass
        except Exception:
            # Silent fail for any other cleanup errors during destruction
            pass 