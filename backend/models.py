from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Generate API Models
class GenerateRequest(BaseModel):
    keyword: str

class GenerateResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

# Upload API Models
class UploadRequest(BaseModel):
    title: str
    content: str

class UploadResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None 