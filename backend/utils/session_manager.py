"""
Session management for tracking conversations
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ConversationMessage:
    """Single message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    language: str = "zh-tw"
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "language": self.language,
        }


@dataclass
class Session:
    """User session with conversation history"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    conversation_history: List[dict] = field(default_factory=list)
    language: str = "zh-tw"
    metadata: dict = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            language=self.language
        )
        self.conversation_history.append(message.to_dict())
        self.last_activity = datetime.now()
        
        # Limit history length
        max_length = 50
        if len(self.conversation_history) > max_length:
            self.conversation_history = self.conversation_history[-max_length:]
    
    def get_recent_messages(self, n: int = 10) -> List[dict]:
        """Get recent N messages"""
        return self.conversation_history[-n:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def is_expired(self, timeout_seconds: int) -> bool:
        """Check if session is expired"""
        elapsed = datetime.now() - self.last_activity
        return elapsed.total_seconds() > timeout_seconds
    
    def get_duration(self) -> float:
        """Get session duration in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "duration_seconds": self.get_duration(),
            "message_count": len(self.conversation_history),
            "language": self.language,
            "metadata": self.metadata,
        }


class SessionManager:
    """Manage multiple user sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        self.session_timeout = 3600  # 1 hour default
        self.cleanup_interval = 300  # 5 minutes
        
        logger.info("SessionManager initialized")
    
    async def create_session(self, session_id: str) -> Session:
        """Create new session"""
        session = Session(session_id=session_id)
        self.sessions[session_id] = session
        
        logger.info(f"Session created: {session_id}")
        
        # Start cleanup task if not running
        if not self.cleanup_task or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session:
            session.last_activity = datetime.now()
        return session
    
    async def remove_session(self, session_id: str):
        """Remove session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session removed: {session_id}")
    
    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_ids = []
        
        for session_id, session in self.sessions.items():
            if session.is_expired(self.session_timeout):
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            await self.remove_session(session_id)
            logger.info(f"Expired session cleaned up: {session_id}")
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
    
    async def _cleanup_loop(self):
        """Background task to cleanup expired sessions"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def cleanup_all(self):
        """Clean up all sessions"""
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.remove_session(session_id)
        
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("All sessions cleaned up")
    
    def get_active_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
    
    def get_all_sessions(self) -> List[dict]:
        """Get all session info"""
        return [session.to_dict() for session in self.sessions.values()]
    
    def get_session_stats(self) -> dict:
        """Get session statistics"""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "avg_duration": 0,
                "avg_messages": 0,
            }
        
        total_duration = sum(s.get_duration() for s in self.sessions.values())
        total_messages = sum(len(s.conversation_history) for s in self.sessions.values())
        
        return {
            "total_sessions": len(self.sessions),
            "avg_duration_seconds": total_duration / len(self.sessions),
            "avg_messages_per_session": total_messages / len(self.sessions),
            "languages": list(set(s.language for s in self.sessions.values())),
        }
