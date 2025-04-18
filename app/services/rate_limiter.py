import time
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class RateLimiter:
    def __init__(self, rpm: int = int(os.getenv("OPENAI_RATE_LIMIT_RPM", "60"))):
        self.rpm = rpm
        self.window_size = 60  # 1 minute
        self.requests: Dict[datetime, int] = {}
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> bool:
        async with self.lock:
            now = datetime.now()
            # Remove old entries
            self.requests = {
                ts: count for ts, count in self.requests.items()
                if ts > now - timedelta(seconds=self.window_size)
            }
            
            # Calculate current request count
            current_count = sum(self.requests.values())
            
            if current_count >= self.rpm:
                return False
                
            # Add new request
            self.requests[now] = self.requests.get(now, 0) + 1
            return True
            
    async def wait(self) -> None:
        while not await self.acquire():
            await asyncio.sleep(1)

class OpenAIRateLimiter:
    _instance: Optional['OpenAIRateLimiter'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.rate_limiter = RateLimiter()
        return cls._instance
        
    async def __call__(self, func):
        async def wrapper(*args, **kwargs):
            await self.rate_limiter.wait()
            retry_count = int(os.getenv("OPENAI_RETRY_ATTEMPTS", "3"))
            
            for attempt in range(retry_count):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retry_count - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        return wrapper

# Usage example:
rate_limiter = OpenAIRateLimiter()

@rate_limiter
async def generate_embedding(text: str):
    client = OpenAI()
    response = await client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding 