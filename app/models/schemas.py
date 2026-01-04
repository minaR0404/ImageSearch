from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class ImageMetadata(BaseModel):
    """Image metadata for upload"""
    name: Optional[str] = Field(None, description="Image name")
    description: Optional[str] = Field(None, description="Image description")
    tags: Optional[List[str]] = Field(default_factory=list, description="Image tags")


class ImageUploadResponse(BaseModel):
    """Response for image upload"""
    image_id: UUID = Field(default_factory=uuid4, description="Unique image ID")
    image_url: str = Field(..., description="S3 URL of the uploaded image")
    message: str = Field(default="Image uploaded successfully")


class SearchResult(BaseModel):
    """Single search result"""
    image_id: UUID
    image_url: str
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    metadata: ImageMetadata


class SearchResponse(BaseModel):
    """Response for image search"""
    results: List[SearchResult] = Field(default_factory=list)
    total: int = Field(..., description="Total number of results")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    """Error response"""
    error: dict = Field(..., description="Error details")
