#!/usr/bin/env python3
import os
import time
import random
import string
import requests
from sqlalchemy import create_engine, text

API_URL = os.getenv("API_URL", "http://localhost:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:your_postgres_password@postgres:5432/hybrid_search")


def rand_username(prefix="api_test_"):
    return prefix + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def register_and_login():
    username = rand_username()
    email = f"{username}@example.com"
    password = "password123!"

    # Try register
    r = requests.post(f"{API_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    if r.status_code not in (200, 201):
        # If already exists, just try login
        print(f"Register status: {r.status_code} -> {r.text}")

    # Login
    r = requests.post(f"{API_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    r.raise_for_status()
    token = r.json()["access_token"]
    user = r.json()["user"]
    return token, user


def perform_searches(token):
    headers = {"Authorization": f"Bearer {token}"}

    # First call without chat_session_id to create session
    payload = {
        "query": "What is hybrid search?",
        "index_name": "test_index",
        "num_results": 1
    }
    r = requests.post(f"{API_URL}/search", json=payload, headers=headers)
    r.raise_for_status()
    data = r.json()
    chat_session_id = data.get("chat_session_id")
    print("First search chat_session_id:", chat_session_id)

    # Second call with chat_session_id to append
    payload2 = {
        "query": "Explain it briefly.",
        "index_name": "test_index",
        "num_results": 1,
        "chat_session_id": chat_session_id
    }
    r2 = requests.post(f"{API_URL}/search", json=payload2, headers=headers)
    r2.raise_for_status()

    return chat_session_id


def verify_db(chat_session_id):
    # Optional DB verification
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            msg_count = conn.execute(text(
                "SELECT COUNT(*) FROM chat_messages WHERE chat_session_id = :sid"
            ), {"sid": chat_session_id}).scalar_one()
            print("DB chat_messages for session:", msg_count)
    except Exception as e:
        print("DB verification skipped:", e)


if __name__ == "__main__":
    # Wait a bit in case API just started
    time.sleep(1)
    token, user = register_and_login()
    print("Logged in as:", user["username"]) 
    sid = perform_searches(token)
    print("Inserted via endpoint. chat_session_id=", sid)
    verify_db(sid)
