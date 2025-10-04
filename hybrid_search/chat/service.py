from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from .models import ChatSession, ChatMessage

class ChatService:
    def create_session(self, db: Session, user_id: Optional[int], title: Optional[str] = None) -> ChatSession:
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session(self, db: Session, session_id: int) -> Optional[ChatSession]:
        return db.query(ChatSession).filter(ChatSession.id == session_id).first()

    def add_message(
        self,
        db: Session,
        chat_session_id: int,
        role: str,
        content: str,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        message = ChatMessage(
            chat_session_id=chat_session_id,
            user_id=user_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def list_messages(self, db: Session, chat_session_id: int, limit: int = 200) -> List[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.chat_session_id == chat_session_id)
            .order_by(ChatMessage.id.asc())
            .limit(limit)
            .all()
        )

    def delete_session(self, db: Session, session_id: int) -> None:
        db.query(ChatMessage).filter(ChatMessage.chat_session_id == session_id).delete()
        db.query(ChatSession).filter(ChatSession.id == session_id).delete()
        db.commit()
