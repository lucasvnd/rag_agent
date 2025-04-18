from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Document Processing and Chat API",
    description="API for processing documents and providing chat functionality with RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from api.routes import files, chat, auth

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/")
async def root():
    """Root endpoint to check if the API is running"""
    return {"status": "ok", "message": "Document Processing and Chat API is running"} 