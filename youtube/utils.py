"""
Utility functions for YouTube operations.
"""
from typing import Optional
from .core import YouTubeError

def extract_video_id(url: str) -> str:
    """
    Extract the video ID from a YouTube URL.
    
    Args:
        url: YouTube video URL
            
    Returns:
        str: Video ID
            
    Raises:
        YouTubeError: If the URL is invalid or empty
            
    Examples:
        >>> extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
    """
    if not url:
        raise YouTubeError("URL cannot be empty")
            
    if url.startswith("https://www.youtube.com/watch?v="):
        return url.split("v=")[1].split("&")[0]
        
    elif url.startswith("https://youtu.be/"):
        return url.split("youtu.be/")[1]
        
    # If no recognized format, assume the URL is already an ID
    return url

def validate_video_url(url: str) -> bool:
    """
    Validate if a given URL is a valid YouTube video URL.
    
    Args:
        url: URL to validate
            
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        extract_video_id(url)
        return True
    except YouTubeError:
        return False

def format_transcript(transcript_data: list) -> str:
    """
    Format transcript data into a readable string.
    
    Args:
        transcript_data: List of transcript segments
            
    Returns:
        str: Formatted transcript text
    """
    if not transcript_data:
        return ""
        
    return " ".join([segment["text"] for segment in transcript_data]) 