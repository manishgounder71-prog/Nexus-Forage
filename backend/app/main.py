import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.api.missions import router as missions_router
from app.api.agents import router as agents_router
from app.api.organizations import router as org_router
from app.api.ingest import router as ingest_router
from app.api.memory import router as memory_router
from app.api.domain_packs import router as domain_packs_router
from app.api.websocket import router as ws_router
from app.api.connectors import router as connectors_router
from app.api.analytics import router as analytics_router
from app.api.audit import router as audit_router
from app.pipeline.event_bus import event_bus

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[{settings.PROJECT_NAME}] Starting master backend engine v{settings.VERSION}...")
    await init_db()
    await event_bus.start()
    try:
        from app.api import demo_seed
        await demo_seed.seed_demo_organization()
    except Exception as e:
        print(f"[Startup] demo seed skipped: {e}")
    yield
    await event_bus.stop()
    print(f"[{settings.PROJECT_NAME}] Shutting down backend engine.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(missions_router, prefix=settings.API_V1_STR)
app.include_router(domain_packs_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(org_router, prefix=settings.API_V1_STR)
app.include_router(ingest_router, prefix=settings.API_V1_STR)
app.include_router(memory_router, prefix=settings.API_V1_STR)
app.include_router(connectors_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV,
        "demo_mode": settings.DEMO_MODE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
