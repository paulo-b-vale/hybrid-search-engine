#!/usr/bin/env python3
"""
FastAPI server for Hybrid Search System with Authentication
"""

import os
import sys
import uvicorn
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

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
from chat.service import ChatService

# Import your existing workflow - delay import to avoid circular imports
SearchConfig = None
HybridSearchWorkflow = None

def import_workflow_modules():
    """Import workflow modules to avoid circular imports"""
    global SearchConfig, HybridSearchWorkflow
    try:
        from config.settings import SearchConfig
        from workflows.langgraph_workflow import HybridSearchWorkflow
        print("✅ Successfully imported hybrid search modules")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please check your project structure and adjust imports")
        SearchConfig = None
        HybridSearchWorkflow = None
        return False

# NLTK Setup
import nltk
import logging

logger = logging.getLogger(__name__)

def setup_nltk():
    """
    Setup NLTK data with fallback mechanisms
    """
    try:
        # Use temporary directory that's writable
        import tempfile
        temp_dir = tempfile.gettempdir()
        nltk_temp_dir = os.path.join(temp_dir, 'nltk_data')
        
        # Set NLTK data path to include temp directory first
        nltk_paths = [
            nltk_temp_dir,  # Put temp directory first
            '/usr/local/nltk_data',
            '/home/appuser/nltk_data',
            os.path.expanduser('~/nltk_data'),
            '/usr/share/nltk_data',
            '/usr/local/share/nltk_data'
        ]
        
        # Clear and set NLTK data path
        nltk.data.path.clear()
        for path in nltk_paths:
            nltk.data.path.append(path)
        
        # List of required NLTK data
        required_data = ['punkt', 'stopwords', 'averaged_perceptron_tagger']
        
        # Create temp NLTK directory
        os.makedirs(nltk_temp_dir, exist_ok=True)
        
        for data_name in required_data:
            try:
                # Try to download to temp directory
                logger.info(f"Downloading NLTK data '{data_name}' to {nltk_temp_dir}...")
                nltk.download(data_name, download_dir=nltk_temp_dir, quiet=True)
                logger.info(f"Successfully ensured NLTK data '{data_name}' is available")
                
            except Exception as e:
                logger.warning(f"Could not download NLTK data '{data_name}': {e}")
                # Continue without this data - the application should handle gracefully
                
        logger.info(f"NLTK setup completed using directory: {nltk_temp_dir}")
        
    except Exception as e:
        logger.error(f"NLTK setup failed: {e}")
        logger.info("Continuing without NLTK - some text processing features may be limited")

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
auth_service = AuthService(redis_client, SECRET_KEY)
chat_service = ChatService()

# Global workflow instance
workflow_instance = None

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    global workflow_instance
    
    print("🚀 Starting Hybrid Search API with Authentication...")
    
    # Setup NLTK first (optional) - Skip for now due to permission issues
    # try:
    #     setup_nltk()
    #     print("✅ NLTK setup completed")
    # except Exception as e:
    #     print(f"⚠️ NLTK setup failed: {e}")
    #     print("💡 Continuing without NLTK - some text processing features may be limited")
    print("⚠️ NLTK setup skipped - running without NLTK dependencies")
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("💡 Continuing without database - using in-memory storage")
    
    # Initialize workflow
    if not import_workflow_modules():
        print("⚠️ Workflow modules not available - running in mock mode")
    else:
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
    
    # Yield control back to FastAPI
    yield
    
    # Shutdown
    print("👋 Shutting down Hybrid Search API...")
    # Add any cleanup code here if needed

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query", min_length=1)
    index_name: str = Field(..., description="Name of the search index to use")
    search_method: Optional[str] = Field(None, description="Search method to use")
    num_results: Optional[int] = Field(None, description="Number of results to return", ge=1, le=100)
    chat_session_id: Optional[int] = Field(None, description="Existing chat session id. If not provided, a new session will be created.")

class SearchResponse(BaseModel):
    query: str
    answer: str
    method: str = "hybrid_search"
    num_results: int
    chat_session_id: Optional[int] = None
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

# Create FastAPI app with lifespan
app = FastAPI(
    title="Hybrid Search API",
    description="Advanced search API with LangGraph workflow orchestration and authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # Add the lifespan parameter
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Main search endpoint (POST method) - requires authentication"""
    # Ensure chat session
    chat_session_id = request.chat_session_id
    if chat_session_id is None:
        session = chat_service.create_session(db, user_id=current_user.id, title=request.query[:80])
        chat_session_id = session.id

    # Persist the user message
    try:
        chat_service.add_message(
            db,
            chat_session_id=chat_session_id,
            role="user",
            content=request.query,
            user_id=current_user.id,
            metadata={
                "index_name": request.index_name,
                "search_method": request.search_method,
                "num_results": request.num_results,
            },
        )
    except Exception as e:
        print(f"⚠️ Failed to save user chat message: {e}")

    if not workflow_instance:
        return SearchResponse(
            query=request.query,
            answer=f"Mock response for: {request.query} (User: {current_user.username})",
            method="mock",
            num_results=0,
            chat_session_id=chat_session_id,
            workflow_messages=["Running in mock mode - workflow not initialized"],
            error="Workflow not available"
        )
    
    # Check if workflow is properly initialized
    if not hasattr(workflow_instance, 'coordinator') or workflow_instance.coordinator is None:
        return SearchResponse(
            query=request.query,
            answer=f"Mock response for: {request.query} (User: {current_user.username})",
            method="mock",
            num_results=0,
            chat_session_id=chat_session_id,
            workflow_messages=["Running in mock mode - workflow components not available"],
            error="Workflow components not available"
        )
    
    try:
        result = workflow_instance.run(
            query=request.query,
            index_name=request.index_name,
            search_method=request.search_method,
            num_results=request.num_results
        )
        
        # Persist assistant message if available
        try:
            answer_text = result.get("answer") if isinstance(result, dict) else None
            if answer_text:
                chat_service.add_message(
                    db,
                    chat_session_id=chat_session_id,
                    role="assistant",
                    content=answer_text,
                    user_id=current_user.id,
                    metadata={k: v for k, v in result.items() if k not in {"answer"}},
                )
        except Exception as e:
            print(f"⚠️ Failed to save assistant chat message: {e}")

        return SearchResponse(**{**result, "chat_session_id": chat_session_id})
        
    except Exception as e:
        print(f"Search error: {e}")
        # Return a mock response instead of raising an error
        return SearchResponse(
            query=request.query,
            answer=f"Mock response for: {request.query} (User: {current_user.username})",
            method="mock",
            num_results=0,
            chat_session_id=chat_session_id,
            workflow_messages=[f"Workflow error: {str(e)}"],
            error=f"Search failed: {str(e)}"
        )

@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """Handle 422 validation errors and log the request details"""
    print(f"🚨 422 Validation Error from {request.client.host}:{request.client.port}")
    print(f"Request method: {request.method}")
    print(f"Request URL: {request.url}")
    print(f"Request headers: {dict(request.headers)}")
    
    # Try to get the request body
    try:
        body = await request.body()
        print(f"Request body: {body.decode()}")
    except Exception as e:
        print(f"Could not read request body: {e}")
    
    # Return the original 422 response
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=422,
        content={"detail": exc.detail}
    )

@app.get("/search", response_model=SearchResponse, tags=["Search"])
async def search_get(
    query: str = Query(..., description="The search query"),
    index_name: str = Query(..., description="Name of the search index to use"),
    search_method: Optional[str] = Query(None, description="Search method to use"),
    num_results: Optional[int] = Query(None, description="Number of results", ge=1, le=100),
    chat_session_id: Optional[int] = Query(None, description="Existing chat session id. If not provided, a new session will be created."),
    current_user: User = Depends(get_current_user)
):
    """Search endpoint (GET method) - requires authentication"""
    request = SearchRequest(
        query=query,
        index_name=index_name,
        search_method=search_method,
        num_results=num_results,
        chat_session_id=chat_session_id
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