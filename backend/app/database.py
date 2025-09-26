"""
SQLite database setup and operations for conversation storage
"""
import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime


class Database:
    """Simple SQLite database for storing conversations"""
    
    def __init__(self, db_path: str = "chatbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster session_id queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_id ON conversations(session_id)
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")
    
    def save_message(self, session_id: str, role: str, content: str) -> int:
        """
        Save a message to the database
        
        Args:
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
            
        Returns:
            Message ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (session_id, role, content)
            VALUES (?, ?, ?)
        ''', (session_id, role, content))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_conversation(self, session_id: str) -> List[Dict]:
        """
        Get all messages for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, role, content, created_at
            FROM conversations
            WHERE session_id = ?
            ORDER BY created_at ASC
        ''', (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            messages.append({
                'id': row[0],
                'role': row[1],
                'content': row[2],
                'created_at': row[3]
            })
        
        return messages
    
    def get_all_sessions(self) -> List[str]:
        """Get all unique session IDs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT session_id
            FROM conversations
            ORDER BY MAX(created_at) DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def delete_conversation(self, session_id: str) -> int:
        """
        Delete all messages for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of deleted messages
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM conversations
            WHERE session_id = ?
        ''', (session_id,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count


# Global database instance
db = Database()

