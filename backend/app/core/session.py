"""
Cashback Optimization Engine - Session Management
Sprint 2: Simple in-memory session storage for MVP

For production, replace with Redis or database-backed sessions.
"""

from typing import Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime, timedelta


class SessionStore:
    """
    In-memory session storage.
    
    Maps session_token -> user_id for authenticated sessions.
    Sessions expire after 24 hours of inactivity.
    """
    
    def __init__(self):
        # session_token: (user_id, last_activity)
        self._sessions: Dict[str, tuple[UUID, datetime]] = {}
        self.session_timeout = timedelta(hours=24)
    
    def create_session(self, user_id: UUID) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            session_token: Unique session identifier
        """
        session_token = str(uuid4())
        self._sessions[session_token] = (user_id, datetime.utcnow())
        return session_token
    
    def get_user_id(self, session_token: str) -> Optional[UUID]:
        """
        Get user_id from session token.
        
        Args:
            session_token: Session identifier
            
        Returns:
            user_id if session is valid, None if expired or not found
        """
        if session_token not in self._sessions:
            return None
        
        user_id, last_activity = self._sessions[session_token]
        
        # Check if session expired
        if datetime.utcnow() - last_activity > self.session_timeout:
            # Expired - remove it
            del self._sessions[session_token]
            return None
        
        # Update last activity
        self._sessions[session_token] = (user_id, datetime.utcnow())
        return user_id
    
    def delete_session(self, session_token: str) -> bool:
        """
        Delete a session (logout).
        
        Args:
            session_token: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        if session_token in self._sessions:
            del self._sessions[session_token]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove all expired sessions."""
        now = datetime.utcnow()
        expired = [
            token for token, (_, last_activity) in self._sessions.items()
            if now - last_activity > self.session_timeout
        ]
        for token in expired:
            del self._sessions[token]


# Singleton instance
_session_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get or create the global session store."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
