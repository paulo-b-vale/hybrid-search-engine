import os
import redis
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# Alembic (for migrations)
try:
    from alembic import command as alembic_command
    from alembic.config import Config as AlembicConfig
except Exception:  # pragma: no cover - alembic optional at import time
    alembic_command = None
    AlembicConfig = None

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

def _get_project_root() -> str:
    """Return absolute path to project root (directory containing alembic.ini)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _run_alembic_upgrade():
    """Run Alembic migrations up to head. If Alembic is not available, fallback to create_all."""
    if alembic_command is None or AlembicConfig is None:
        # Fallback: best-effort table creation (dev-only)
        Base.metadata.create_all(bind=engine)
        return

    project_root = _get_project_root()
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    alembic_dir = os.path.join(project_root, "alembic")

    # Configure Alembic programmatically
    cfg = AlembicConfig(alembic_ini_path) if os.path.exists(alembic_ini_path) else AlembicConfig()
    cfg.set_main_option("script_location", alembic_dir)
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

    # Detect baseline: if schema exists without alembic, stamp initial
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    has_alembic_table = "alembic_version" in existing_tables

    # If users table exists but alembic not initialized, stamp to initial baseline (0001)
    if not has_alembic_table and ("users" in existing_tables or "user_sessions" in existing_tables):
        try:
            alembic_command.stamp(cfg, "0001_initial_users_sessions")
        except Exception:
            # If stamping fails, fallback to no-op; upgrade might fail if schema diverges
            pass

    # Finally, upgrade to head (applies any pending migrations, including chat tables)
    alembic_command.upgrade(cfg, "head")


def init_database():
    """Initialize database by running migrations (preferred) or creating tables (fallback)."""
    try:
        _run_alembic_upgrade()
    except Exception:
        # Fallback in case migrations fail (do not crash server startup)
        Base.metadata.create_all(bind=engine)