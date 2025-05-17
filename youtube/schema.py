"""
Schema definitions for YouTube tools.
"""
from typing import Optional
from pydantic import BaseModel, Field

class TranscriptRequest(BaseModel):
    """
    Request model for video transcript.
    """
    url: str = Field(
        ...,
        description="URL of the YouTube video (formats: youtube.com/watch?v=ID, youtu.be/ID, or direct ID)"
    )

class TranscriptResponse(BaseModel):
    """
    Response model for video transcript.
    """
    success: bool = Field(
        ...,
        description="Whether the transcript was successfully retrieved"
    )
    transcript: Optional[str] = Field(
        None,
        description="The video transcript if available"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if the operation failed"
    ) 