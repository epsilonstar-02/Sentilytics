"""
Database Configuration Module
Handles PostgreSQL connection and configuration
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'youtube_analytics'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Create Database URL
DATABASE_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# SQLAlchemy Engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=pool.QueuePool,
    pool_size=10,  # Maximum number of connections to keep open
    max_overflow=20,  # Maximum number of connections that can be created beyond pool_size
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for SQL query logging
)

# SQLAlchemy Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Ensures proper cleanup and connection handling.
    
    Usage:
        with get_db_session() as session:
            result = session.execute("SELECT * FROM products")
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db_connection():
    """
    Get a raw database connection (for use with psycopg2 directly).
    
    Returns:
        psycopg2 connection object
    """
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def test_connection():
    """
    Test the database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        from sqlalchemy import text
        with get_db_session() as session:
            result = session.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def get_connection_string():
    """
    Get the database connection string (without password for logging).
    
    Returns:
        str: Safe connection string
    """
    return (
        f"postgresql://{DB_CONFIG['user']}:****"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )


def close_all_connections():
    """
    Close all database connections.
    Useful for cleanup during shutdown.
    """
    engine.dispose()
    logger.info("All database connections closed")


# Export commonly used functions
__all__ = [
    'engine',
    'SessionLocal',
    'Base',
    'get_db_session',
    'get_db_connection',
    'test_connection',
    'get_connection_string',
    'close_all_connections',
    'DB_CONFIG'
]


if __name__ == "__main__":
    """Test the database connection when run directly."""
    from sqlalchemy import text
    print("=" * 60)
    print("YouTube Analytics - Database Configuration Test")
    print("=" * 60)
    print(f"\nConnection String: {get_connection_string()}")
    print("\nTesting connection...")
    
    if test_connection():
        print("\n✅ SUCCESS: Database is ready!")
        
        # Test query
        try:
            with get_db_session() as session:
                result = session.execute(text("SELECT name FROM products"))
                products = result.fetchall()
                if products:
                    print(f"\nProducts in database: {len(products)}")
                    for product in products:
                        print(f"  - {product[0]}")
                else:
                    print("\nNo products found. Database is empty.")
        except Exception as e:
            print(f"\n⚠️  Could not query products: {e}")
    else:
        print("\n❌ FAILED: Could not connect to database")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'youtube_analytics' exists")
        print("  3. Database credentials in .env file are correct")
        print("  4. Database user has proper permissions")
    
    print("\n" + "=" * 60)
