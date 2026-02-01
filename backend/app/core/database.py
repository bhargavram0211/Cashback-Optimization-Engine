"""
GetCardIQ - Database Utilities
Database session management and dependencies
"""

import os
from typing import Generator

from sqlmodel import Session, create_engine

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cashback_user:cashback_pass_local_dev_only@db:5432/cashback_db"
)

# Create engine (singleton)
engine = create_engine(DATABASE_URL, echo=True)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    
    Yields a session that is automatically closed after use.
    Used with FastAPI's Depends() for automatic session management.
    
    Usage:
        @app.get("/endpoint")
        def my_endpoint(session: Session = Depends(get_session)):
            # Use session here
            pass
    """
    with Session(engine) as session:
        yield session

