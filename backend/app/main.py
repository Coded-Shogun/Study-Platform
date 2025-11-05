from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .utils.database import engine, Base
from .api import quiz, progress, labs, auth

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up CompTIA Cloud+ Study Platform API")
    yield
    # Shutdown
    print("Shutting down API")

app = FastAPI(
    title="CompTIA Cloud+ Study Platform",
    description="Comprehensive study platform for Cloud+ certification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(labs.router, prefix="/api/labs", tags=["labs"])

@app.get("/")
async def root():
    return {
        "message": "CompTIA Cloud+ Study Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cloud-plus-api"}
