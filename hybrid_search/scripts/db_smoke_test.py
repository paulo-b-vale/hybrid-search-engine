#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# Ensure local imports resolve
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import text
from auth.database import init_database, SessionLocal, engine, DATABASE_URL
from auth.models import User
from auth.service import pwd_context


def mask_url(url: str) -> str:
    try:
        # Mask password if present
        if "@" in url and "://" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest and ":" in rest.split("@", 1)[0]:
                creds, host = rest.split("@", 1)
                user, _ = creds.split(":", 1)
                return f"{scheme}://{user}:***@{host}"
        return url
    except Exception:
        return url


def main():
    print("== DB Smoke Test ==")
    print(f"DATABASE_URL: {mask_url(DATABASE_URL)}")

    print("Running migrations...")
    init_database()
    print("Migrations complete.")

    db = SessionLocal()
    try:
        # Ensure there is a test user
        ts_suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        username = f"db_test_user_{ts_suffix}"
        email = f"{username}@example.com"
        password_hash = pwd_context.hash("password123!")

        user = User(username=username, email=email, hashed_password=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user id={user.id}, username={user.username}")

        # Create chat session via SQL
        res = db.execute(text(
            """
            INSERT INTO chat_sessions (user_id, title) VALUES (:uid, :title) RETURNING id
            """
        ), {"uid": user.id, "title": "Smoke Test Session"})
        chat_session_id = res.scalar_one()
        db.commit()
        print(f"Created chat_session id={chat_session_id}")

        # Add messages via SQL
        import json
        db.execute(text(
            """
            INSERT INTO chat_messages (chat_session_id, user_id, role, content, message_metadata)
            VALUES (:sid, :uid, :role, :content, :meta)
            """
        ), {
            "sid": chat_session_id,
            "uid": user.id,
            "role": "user",
            "content": "Hello, database!",
            "meta": json.dumps({"test": True}),
        })

        db.execute(text(
            """
            INSERT INTO chat_messages (chat_session_id, user_id, role, content, message_metadata)
            VALUES (:sid, :uid, :role, :content, :meta)
            """
        ), {
            "sid": chat_session_id,
            "uid": user.id,
            "role": "assistant",
            "content": "Acknowledged. DB is reachable.",
            "meta": json.dumps({"reply": True}),
        })
        db.commit()

        # Validate counts
        msg_count = db.execute(text("SELECT COUNT(*) FROM chat_messages WHERE chat_session_id = :sid"), {"sid": chat_session_id}).scalar_one()
        print(f"Chat messages inserted: {msg_count}")

        # Show current alembic version
        try:
            with engine.connect() as conn:
                res = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                if res:
                    print(f"Alembic version: {res[0]}")
        except Exception as e:
            print(f"Could not read alembic version: {e}")

        print("Smoke test OK.")
        return 0
    except Exception as e:
        print(f"Smoke test FAILED: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
