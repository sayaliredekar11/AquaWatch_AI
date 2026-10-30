import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 1. Load environment variables from the .env file
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
load_dotenv()

# 2. Fetch the Database URL from environment variables
# Fallback to a placeholder URL if not set in .env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/aquawatch",
)

# 3. Create the SQLAlchemy Engine (Synchronous)
# The engine manages the pool of connections to the PostgreSQL database.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Automatically tests connections before using them
    echo=False,          # Set to True to print all generated SQL queries in the console
)

# 4. Session factory (SessionLocal)
# Each instance of SessionLocal represents an individual database session.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 5. Declarative Base class using SQLAlchemy 2.x standard
# All future ORM models will inherit from this Base class.
class Base(DeclarativeBase):
    pass

# 6. Database Dependency for FastAPI (get_db)
# This generator function creates a fresh session for each incoming HTTP request
# and guarantees that the session is closed when the request finishes, even if errors occur.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
