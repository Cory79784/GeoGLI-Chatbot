#!/usr/bin/env python3
"""
Initialize the SQLite database for the chatbot
"""
from app.database import db

if __name__ == "__main__":
    print("Initializing database...")
    # Database is automatically initialized when imported
    print(f"Database initialized successfully at: {db.db_path}")

