import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.schemas import MessageResponse, HealthResponse, DbHealthResponse
from app.routers.auth import router as auth_router
from app.routers.water_bodies import router as water_bodies_router
from app.routers.water_quality import router as water_quality_router
from app.routers.gis import router as gis_router
from app.routers.dashboard import router as dashboard_router
from app.routers.predictions import router as predictions_router

# Configure logging for AquaWatch backend
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aquawatch")


# 1. Lifespan event handler to ensure database tables are created on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database tables safely without dropping existing data.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")
    yield


# 2. Initialize FastAPI application
app = FastAPI(
    title="AquaWatch AI Backend",
    description="Intelligent Water Quality Monitoring & Pollution Prediction Platform - Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# 3. Configure CORS middleware for local frontend development (Vite port 5173, React port 3000)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Include Routers
app.include_router(auth_router)
app.include_router(water_bodies_router)
app.include_router(water_quality_router)
app.include_router(gis_router)
app.include_router(dashboard_router)
app.include_router(predictions_router)


# ==========================================================
# Day 1 Foundation Endpoints
# ==========================================================

# 5. GET / - Welcome endpoint
@app.get("/", response_model=MessageResponse, tags=["General"])
def read_root():
    """
    Root endpoint for AquaWatch AI Backend.
    Provides a simple welcome message to verify the service is running.
    """
    return {"message": "Welcome to AquaWatch AI Backend"}


# 6. GET /health - Basic application health check
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Basic health check endpoint.
    Indicates whether the FastAPI server process is alive and responsive.
    Note: Does not depend on database availability.
    """
    return {"status": "healthy"}


# 7. GET /health/db - Database connectivity check
@app.get("/health/db", response_model=DbHealthResponse, tags=["Health"])
def db_health_check(db: Session = Depends(get_db)):
    """
    Database connectivity check endpoint.
    Executes a lightweight 'SELECT 1' test query against PostgreSQL.
    Credentials and sensitive connection parameters are masked and never exposed.
    """
    try:
        # Execute test query
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        # Log internal error without exposing sensitive connection credentials to the client
        logger.error(f"Database connectivity check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. Ensure PostgreSQL is running and DATABASE_URL in .env is configured correctly.",
        )
