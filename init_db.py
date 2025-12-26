#!/usr/bin/env python3
"""
Database Initialization Script for Agent API
This script creates all necessary database tables
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
from models import Base

def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
        return True
        
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)