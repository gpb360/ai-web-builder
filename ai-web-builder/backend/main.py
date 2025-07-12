from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import components, auth, projects, platform, ai
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AI Web Builder API",
    description="Backend API for AI-powered web component generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(components.router, prefix="/api/components", tags=["components"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(platform.router, prefix="/api/platform", tags=["platform"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

@app.get("/")
async def root():
    return {"message": "AI Web Builder API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}