"""
Chat manager for in-memory conversation storage.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid


class ChatManager:
    """Manages chat sessions and conversation history in memory."""

    def __init__(
        self,
        max_history_length: int = 20,
        session_timeout_minutes: int = 60,
    ):
        """
        Initialize chat manager.

        Args:
            max_history_length: Maximum number of messages to keep per session
            session_timeout_minutes: Minutes before a session is considered expired
        """
        self.sessions: Dict[str, Dict] = {}
        self.max_history_length = max_history_length
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        print(f"✓ Chat Manager initialized (max history: {max_history_length}, timeout: {session_timeout_minutes}m)")

    def create_session(self) -> str:
        """
        Create a new chat session.

        Returns:
            Unique session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "messages": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
        }
        print(f"Created new session: {session_id}")
        return session_id

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to session history.

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content

        Raises:
            ValueError: If session doesn't exist
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        # Add message with timestamp
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self.sessions[session_id]["messages"].append(message)

        # Update last activity
        self.sessions[session_id]["last_activity"] = datetime.now()

        # Trim history if it exceeds max length
        if len(self.sessions[session_id]["messages"]) > self.max_history_length:
            # Keep only the most recent messages
            self.sessions[session_id]["messages"] = self.sessions[session_id]["messages"][
                -self.max_history_length :
            ]

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries

        Raises:
            ValueError: If session doesn't exist
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        return self.sessions[session_id]["messages"]

    def get_recent_history(
        self, session_id: str, count: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get the most recent messages from a session.

        Args:
            session_id: Session identifier
            count: Number of recent messages to retrieve

        Returns:
            List of recent message dictionaries

        Raises:
            ValueError: If session doesn't exist
        """
        history = self.get_history(session_id)
        return history[-count:]

    def clear_session(self, session_id: str) -> None:
        """
        Clear a session's history (keep session active).

        Args:
            session_id: Session identifier

        Raises:
            ValueError: If session doesn't exist
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        self.sessions[session_id]["messages"] = []
        self.sessions[session_id]["last_activity"] = datetime.now()
        print(f"Cleared history for session: {session_id}")

    def delete_session(self, session_id: str) -> None:
        """
        Completely delete a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"Deleted session: {session_id}")

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists, False otherwise
        """
        return session_id in self.sessions

    def is_session_expired(self, session_id: str) -> bool:
        """
        Check if a session has expired.

        Args:
            session_id: Session identifier

        Returns:
            True if session is expired, False otherwise
        """
        if session_id not in self.sessions:
            return True

        last_activity = self.sessions[session_id]["last_activity"]
        return datetime.now() - last_activity > self.session_timeout

    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions to prevent memory bloat.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired_sessions = [
            sid
            for sid, data in self.sessions.items()
            if now - data["last_activity"] > self.session_timeout
        ]

        for sid in expired_sessions:
            del self.sessions[sid]

        if expired_sessions:
            print(f"Cleaned up {len(expired_sessions)} expired session(s)")

        return len(expired_sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information about a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session information or None if not found
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "message_count": len(session["messages"]),
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat(),
            "is_expired": self.is_session_expired(session_id),
        }

    def get_stats(self) -> Dict:
        """
        Get statistics about all sessions.

        Returns:
            Dictionary with session statistics
        """
        total_messages = sum(
            len(session["messages"]) for session in self.sessions.values()
        )
        active_sessions = sum(
            1 for sid in self.sessions if not self.is_session_expired(sid)
        )

        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "avg_messages_per_session": (
                total_messages / len(self.sessions) if self.sessions else 0
            ),
        }
