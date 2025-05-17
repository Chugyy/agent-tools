"""
YouTube tool declarations.
"""
from typing import Optional
from pydantic import BaseModel, Field
from ai_agent.app.tools.registry import register
from .core import YouTubeCore, YouTubeError, YouTubeAPIError
from .schema import TranscriptRequest, TranscriptResponse

# Initialize core functionality
youtube = YouTubeCore()

@register(name="youtube_transcript")
def get_video_transcript(request: TranscriptRequest) -> TranscriptResponse:
    """
    Get the transcript of a YouTube video.
    
    This tool uses the YouTube API to retrieve the transcript (subtitles) of a video.
    It supports various URL formats and handles errors gracefully.
    
    Args:
        request: TranscriptRequest object containing the video URL
        
    Returns:
        TranscriptResponse object containing the transcript or error details
        
    Examples:
        >>> request = TranscriptRequest(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        >>> response = get_video_transcript(request)
        >>> print(response.transcript if response.success else response.error)
    """
    try:
        transcript = youtube.get_transcript(request.url)
        
        # Check if the response is an error message
        if transcript.startswith("Erreur"):
            return TranscriptResponse(
                success=False,
                error=transcript
            )
            
        return TranscriptResponse(
            success=True,
            transcript=transcript
        )
        
    except (YouTubeError, YouTubeAPIError) as e:
        return TranscriptResponse(
            success=False,
            error=str(e)
        )
        
    except Exception as e:
        return TranscriptResponse(
            success=False,
            error=f"Erreur inattendue: {str(e)}"
        ) 