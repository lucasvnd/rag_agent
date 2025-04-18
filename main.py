from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Document Processing API with Template Suggestions",
    description="API for processing documents using RAG and suggesting appropriate templates",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from api.routes import file, chat

# Include routers
app.include_router(file.router, prefix="/file", tags=["file"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/health")
async def health_check():
    """Health check endpoint to verify if the API is running"""
    return {"status": "ok", "message": "Document Processing API is running"}

@app.get("/")
async def root():
    """Root endpoint that redirects to documentation"""
    return {"status": "ok", "message": "Document Processing API is running", "documentation": "/docs"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True) 