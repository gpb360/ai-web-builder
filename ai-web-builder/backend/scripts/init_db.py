#!/usr/bin/env python3
"""
Database initialization script
Usage: python scripts/init_db.py [--seed] [--clear]
"""

import asyncio
import argparse
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_db, close_db, async_session_maker
from database.seed_data import create_seed_data, clear_seed_data

async def main():
    parser = argparse.ArgumentParser(description='Initialize the database')
    parser.add_argument('--seed', action='store_true', help='Create seed data')
    parser.add_argument('--clear', action='store_true', help='Clear seed data')
    parser.add_argument('--reset', action='store_true', help='Reset database (drop and recreate)')
    
    args = parser.parse_args()
    
    try:
        print("🔄 Initializing database...")
        
        if args.reset:
            print("⚠️  Resetting database (this will drop all data)")
            from database.connection import engine, Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                print("🗑️  All tables dropped")
        
        # Initialize database tables
        await init_db()
        print("✅ Database tables created/updated")
        
        # Handle seed data
        async with async_session_maker() as session:
            if args.clear:
                print("🧹 Clearing seed data...")
                await clear_seed_data(session)
            
            if args.seed:
                print("🌱 Creating seed data...")
                await create_seed_data(session)
        
        print("🎉 Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())