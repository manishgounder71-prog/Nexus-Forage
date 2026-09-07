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

# CORS Configuration for Local, Docker, and Vercel Deployments
origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_origin_regex=r"^https?://.*" if "*" in origins else r"^https?://.*\.vercel\.app$",
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

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Service landing endpoint providing system status and API navigation links."""
    return {
        "name": settings.PROJECT_NAME,
        "status": "ONLINE",
        "version": settings.VERSION,
        "environment": settings.ENV,
        "docs_url": "/docs",
        "health_url": "/health",
        "ping_url": "/ping",
        "api_v1": settings.API_V1_STR
    }

@app.api_route("/ping", methods=["GET", "HEAD"])
async def ping():
    """Ultra-fast keepalive probe for UptimeRobot / uptime bots to prevent sleeping."""
    return {"pong": True, "status": "UP"}

@app.api_route("/health", methods=["GET", "HEAD"])
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
    port = int(os.environ.get("PORT", 8000))
    reload = settings.ENV == "development"
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload)
