from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

# Define the base for declarative models. This Base will be used by all models.
Base = declarative_base()

# Database URL - using SQLite for simplicity, stored in the root directory
DATABASE_URL = 'sqlite:///sms_database.db'

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a sessionmaker
Session = sessionmaker(bind=engine)

def init_db():
    """
    Initializes the database by creating tables for all models defined
    under the Base.
    """
    # Import all models here to ensure they are registered with Base.metadata
    # from models.users import User
    # from models.transactions import Transaction
    from models.users import User
    from models.transactions import Transaction
    
    print("Initializing database tables...")
    Base.metadata.create_all(engine)
    print("Database tables created/checked.")

@contextmanager
def get_db():
    """
    Provides a new SQLAlchemy session.
    Use this in a 'with' statement for automatic session closing.
    """
    session = Session()
    try:
        yield session
    finally:
        session.close()

# When database.py is imported, Base and engine are available for other modules.
# We call init_db directly here for simplicity, typically done once at app startup.
# init_db() will be called from app.py to ensure all models are loaded.
