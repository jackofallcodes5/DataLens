from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.routes import health, projects, datasets, profiling, cleaning, visualization, exports, etl

# Initialize DB tables
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    description="Data Cleaning, Quality Analysis, Visualization and Export Platform",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(profiling.router, prefix="/api")
app.include_router(cleaning.router, prefix="/api")
app.include_router(visualization.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(etl.router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }
