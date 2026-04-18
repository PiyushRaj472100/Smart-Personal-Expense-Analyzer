from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys
from dotenv import load_dotenv

# Ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

load_dotenv(os.path.join(BASE_DIR, ".env"))

from backend.routes.auth import auth_router
from backend.routes.profile import profile_router
from backend.routes.transactions import transactions_router
from backend.routes.dashboard import dashboard_router
from backend.routes.analytics import analytics_router

app = FastAPI(title="Smart Expense Analyzer API")

# Comma-separated origins; use * only for local/dev convenience.
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
if cors_origins_env.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

# CORS - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (optional - for serving HTML)
# Uncomment if you want to serve frontend from backend
# static_path = os.path.join(BASE_DIR, "../frontend")
# if os.path.exists(static_path):
#     app.mount("/static", StaticFiles(directory=static_path), name="static")

# API Routes - Match frontend expectations
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(profile_router, prefix="/api/profile", tags=["Profile"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])

@app.get("/")
def root():
    return {
        "message": "Smart Expense Analyzer API Running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)