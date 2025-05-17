from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

class MediaType(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"

class MediaMetadata(BaseModel):
    media_id: str
    original_url: Union[HttpUrl, str]
    local_path: str
    media_type: MediaType
    content_type: str
    size: int
    session_id: Optional[str] = None
    processed: bool = False
    processed_content: Optional[str] = None
    download_date: datetime = Field(default_factory=datetime.now)
    
    # Optional fields that were added in server.py
    reference_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

class MediaReference(BaseModel):
    """Schema for referencing media in an API request."""
    url: Union[HttpUrl, str]
    reference_id: Optional[str] = Field(None, description="Custom ID to reference this media in the prompt.")
    title: Optional[str] = Field(None, description="Optional title for the media.")
    description: Optional[str] = Field(None, description="Optional description for the media.")

class MediaInfo(BaseModel):
    """Schema for returning information about processed media."""
    media_id: str
    original_url: Union[HttpUrl, str]
    media_type: MediaType
    content_type: str
    size: int
    reference_id: Optional[str] = None
    download_date: datetime
    processed: bool = False
    title: Optional[str] = None
    description: Optional[str] = None
    # processed_content: Optional[str] = None # Not typically returned in list, but in extraction

# Potentially add Pydantic schemas here if tool arguments become complex
# Example:
# from pydantic import BaseModel, HttpUrl
#
# class LoadMediaSchema(BaseModel):
#     url: HttpUrl
#     session_id: Optional[str] = None
#
# class ExtractMediaSchema(BaseModel):
#     media_id: str
#     max_pages: int = 10 