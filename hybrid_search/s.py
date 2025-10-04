import os

# A dictionary to hold the file paths and their content
# Using triple single quotes ''' to avoid conflicts with docstrings """
project_files = {
    "docker-compose.yml": '''
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    container_name: hybrid_search_postgres
    environment:
      POSTGRES_DB: hybrid_search
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_postgres_password
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - hybrid_search_network

  # Redis for session management
  redis:
    image: redis:7-alpine
    container_name: hybrid_search_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - hybrid_search_network

  # Your FastAPI application
  api:
    build: .
    container_name: hybrid_search_api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:your_postgres_password@postgres:5432/hybrid_search
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-super-secret-key-change-this-in-production
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
    depends_on:
      - postgres
      - redis
    networks:
      - hybrid_search_network
    volumes:
      - .:/app
    command: python server.py

volumes:
  postgres_data:
  redis_data:

networks:
  hybrid_search_network:
    driver: bridge
''',

    "init.sql": '''
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sessions table (backup to Redis)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);

-- Insert a default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, is_superuser) 
VALUES ('admin', 'admin@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', TRUE)
ON CONFLICT (username) DO NOTHING;
''',

    "requirements.txt": '''
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
redis==5.0.1
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
alembic==1.13.1
pydantic==2.5.0
pydantic-settings==2.1.0
''',

    "Dockerfile": '''
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "server.py"]
''',

    ".env": '''
# Database
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/hybrid_search
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-make-it-very-long-and-random
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=true
''',

    "auth/__init__.py": '''
# This file makes the 'auth' directory a Python package.
''',

    "auth/models.py": '''
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
''',

    "auth/database.py": '''
import os
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:your_postgres_password@localhost:5432/hybrid_search")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
''',

    "auth/service.py": '''
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
''',

    "server.py": '''
#!/usr/bin/env python3
"""
FastAPI server for Hybrid Search System with Authentication
"""

import os
import sys
import uvicorn
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Add the current directory to Python path so imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import authentication modules
from auth.database import get_db, init_database, redis_client
from auth.service import AuthService
from auth.models import UserCreate, UserLogin, UserResponse, Token, User

# Import your existing workflow
try:
    from hybrid_search.config.settings import SearchConfig
    from hybrid_search.workflows.langgraph_workflow import HybridSearchWorkflow
    print("✅ Successfully imported hybrid search modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please check your project structure and adjust imports")
    SearchConfig = None
    HybridSearchWorkflow = None

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
auth_service = AuthService(redis_client, SECRET_KEY)

# Pydantic models for API (keeping your existing ones)
class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query", min_length=1)
    index_name: str = Field(..., description="Name of the search index to use")
    search_method: Optional[str] = Field(None, description="Search method to use")
    num_results: Optional[int] = Field(None, description="Number of results to return", ge=1, le=100)

class SearchResponse(BaseModel):
    query: str
    answer: str
    method: str = "hybrid_search"
    num_results: int
    search_results: List[Dict[str, Any]] = []
    content_analysis: Dict[str, Any] = {}
    similarity_analysis: Dict[str, Any] = {}
    validation_results: Dict[str, Any] = {}
    step_times: Dict[str, float] = {}
    total_processing_time: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = 0.0
    workflow_messages: List[str] = []
    quality_score: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    status: str
    workflow_ready: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str = ""

# Create FastAPI app
app = FastAPI(
    title="Hybrid Search API",
    description="Advanced search API with LangGraph workflow orchestration and authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global workflow instance
workflow_instance = None

# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    return user

@app.on_event("startup")
async def startup_event():
    """Initialize the workflow and database when server starts"""
    global workflow_instance
    
    print("🚀 Starting Hybrid Search API with Authentication...")
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    # Initialize workflow
    if not SearchConfig or not HybridSearchWorkflow:
        print("⚠️ Workflow modules not available - running in mock mode")
        return
    
    try:
        config = SearchConfig(
            max_context_tokens=8000,
            max_output_tokens=1024,
            default_search_method="multi_stage",
            default_num_results=5,
        )
        
        workflow_instance = HybridSearchWorkflow(config)
        print("✅ Hybrid Search Workflow initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {e}")
        print("💡 Server will still start but searches will return mock responses")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when server shuts down"""
    print("👋 Shutting down Hybrid Search API...")

# Public endpoints (no authentication required)
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - shows API info"""
    return {
        "message": "Hybrid Search API with Authentication",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "login_endpoint": "/auth/login",
        "search_endpoint": "/search"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    if workflow_instance:
        return HealthResponse(
            status="healthy",
            workflow_ready=True,
            message="All systems operational"
        )
    else:
        return HealthResponse(
            status="degraded",
            workflow_ready=False,
            message="Workflow not initialized - running in mock mode"
        )

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    if auth_service.get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    try:
        db_user = auth_service.create_user(db, user)
        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            is_superuser=db_user.is_superuser,
            created_at=db_user.created_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    try:
        result = auth_service.login_user(db, login_data)
        return Token(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user=UserResponse(
                id=result["user"].id,
                username=result["user"].username,
                email=result["user"].email,
                is_active=result["user"].is_active,
                is_superuser=result["user"].is_superuser,
                created_at=result["user"].created_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/auth/logout", tags=["Authentication"])
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate token"""
    token = credentials.credentials
    auth_service.logout_user(db, token)
    return {"message": "Successfully logged out"}

@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at
    )

# Protected endpoints (authentication required)
@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_post(
    request: SearchRequest, 
    current_user: User = Depends(get_current_user)
):
    """Main search endpoint (POST method) - requires authentication"""
    
    if not workflow_instance:
        return SearchResponse(
            query=request.query,
            answer=f"Mock response for: {request.query} (User: {current_user.username})",
            method="mock",
            num_results=0,
            workflow_messages=["Running in mock mode - workflow not initialized"],
            error="Workflow not available"
        )
    
    try:
        result = workflow_instance.run(
            query=request.query,
            index_name=request.index_name,
            search_method=request.search_method,
            num_results=request.num_results
        )
        
        return SearchResponse(**result)
        
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}"
        )

@app.get("/search", response_model=SearchResponse, tags=["Search"])
async def search_get(
    query: str = Query(..., description="The search query"),
    index_name: str = Query(..., description="Name of the search index to use"),
    search_method: Optional[str] = Query(None, description="Search method to use"),
    num_results: Optional[int] = Query(None, description="Number of results", ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Search endpoint (GET method) - requires authentication"""
    request = SearchRequest(
        query=query,
        index_name=index_name,
        search_method=search_method,
        num_results=num_results
    )
    return await search_post(request, current_user)

def main():
    """Main function to run the server"""
    print("🔧 Hybrid Search API Server with Authentication")
    print("=" * 60)
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Reload: {reload}")
    print(f"Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    print("=" * 60)
    
    # Run the server
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[current_dir] if reload else None,
        log_level="info"
    )

if __name__ == "__main__":
    main()
'''
}

def create_project_structure():
    """
    Creates the directories and files for the project.
    """
    print("🚀 Starting project setup...")

    for file_path, content in project_files.items():
        # Get the directory name from the file path
        directory = os.path.dirname(file_path)

        # Create the directory if it doesn't exist
        if directory and not os.path.exists(directory):
            print(f"Creating directory: {directory}/")
            os.makedirs(directory)

        # Write the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # .strip() removes leading/trailing whitespace from the multiline string
                f.write(content.strip())
            print(f"✅ Created file: {file_path}")
        except IOError as e:
            print(f"❌ Error creating file {file_path}: {e}")

    print("\n🎉 Project setup complete!")
    print("You can now build and run the services with: docker-compose up --build -d")

if __name__ == "__main__":
    create_project_structure()