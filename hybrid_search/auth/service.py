import json
import redis
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status

from .models import User, UserSession, UserCreate, UserLogin
from .database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, redis_client: redis.Redis, secret_key: str, algorithm: str = "HS256"):
        self.redis_client = redis_client
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt, expire

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def create_user(self, db: Session, user: UserCreate) -> User:
        hashed_password = self.get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(db, username)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    def login_user(self, db: Session, login_data: UserLogin) -> dict:
        user = self.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )

        # Create access token
        access_token, expire_time = self.create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )

        # Store session in Redis
        session_data = {
            "user_id": user.id,
            "username": user.username,
            "expires_at": expire_time.isoformat(),
            "is_active": user.is_active,
            "is_superuser": user.is_superuser
        }
        
        # Store in Redis with expiration
        self.redis_client.setex(
            f"session:{access_token}",
            timedelta(minutes=self.access_token_expire_minutes),
            json.dumps(session_data)
        )

        # Also store in database as backup
        db_session = UserSession(
            user_id=user.id,
            session_token=access_token,
            expires_at=expire_time
        )
        db.add(db_session)
        db.commit()

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "user": user
        }

    def get_current_user(self, db: Session, token: str) -> Optional[User]:
        # First check Redis
        session_data = self.redis_client.get(f"session:{token}")
        if session_data:
            session_info = json.loads(session_data)
            user_id = session_info["user_id"]
            return self.get_user_by_id(db, user_id)
        
        # Fallback to JWT verification
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        username = payload.get("sub")
        if username is None:
            return None
        
        user = self.get_user_by_username(db, username)
        return user

    def logout_user(self, db: Session, token: str):
        # Remove from Redis
        self.redis_client.delete(f"session:{token}")
        
        # Remove from database
        db.query(UserSession).filter(UserSession.session_token == token).delete()
        db.commit()

    def cleanup_expired_sessions(self, db: Session):
        """Clean up expired sessions from database"""
        now = datetime.utcnow()
        db.query(UserSession).filter(UserSession.expires_at < now).delete()
        db.commit()