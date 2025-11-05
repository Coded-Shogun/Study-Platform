from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .utils.database import engine, Base
from .api import quiz, progress, labs, auth, admin
from .middleware import limiter, SecurityHeadersMiddleware, RequestLogMiddleware
from .config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting up {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Rate limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    yield
    # Shutdown
    print("Shutting down API")

app = FastAPI(
    title=settings.APP_NAME,
    description="Comprehensive multi-level study platform with admin course management",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Request logging middleware (optional)
if settings.DEBUG:
    app.add_middleware(RequestLogMiddleware)

# CORS middleware - Use environment variable for allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(labs.router, prefix="/api/labs", tags=["labs"])
app.include_router(admin.router, tags=["admin"])


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "study-platform-api",
        "version": settings.APP_VERSION
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors
    """
    if settings.DEBUG:
        # In debug mode, show the error details
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        # In production, hide error details
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
