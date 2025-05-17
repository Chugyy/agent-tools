"""
Core functionality for YouTube tools.
"""
import requests
from typing import Optional, Dict, Any
from app.utils.settings import get_settings
from app.utils.logging import get_logger
from .utils import extract_video_id, format_transcript

logger = get_logger(__name__)
settings = get_settings()

class YouTubeError(Exception):
    """Base exception for YouTube operations."""
    pass

class YouTubeAPIError(YouTubeError):
    """Raised when the YouTube API returns an error."""
    pass

class YouTubeCore:
    """
    Core class for YouTube operations.
    Handles all the low-level interactions with YouTube APIs.
    """
    
    def __init__(self):
        """Initialize YouTube core functionality."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Validate API key
        if not self.settings.api_keys.rapid_api:
            raise YouTubeError("RapidAPI key is missing. Please configure RAPID_API_KEY in environment variables.")
            
        self.api_key = self.settings.api_keys.rapid_api
        self.headers = {
            "x-rapidapi-host": "youtube-v2.p.rapidapi.com",
            "x-rapidapi-key": self.api_key
        }
    
    def _make_api_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the YouTube API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            YouTubeAPIError: If the API request fails
        """
        try:
            # Log API request (with masked key)
            masked_key = f"{'*' * (len(self.api_key) - 4)}{self.api_key[-4:]}"
            self.logger.debug(f"Making API request to {endpoint} with key: {masked_key}")
            
            response = requests.get(
                f"https://youtube-v2.p.rapidapi.com/{endpoint}",
                headers=self.headers,
                params=params
            )
            
            if response.status_code != 200:
                raise YouTubeAPIError(f"API request failed with status code: {response.status_code}")
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise YouTubeAPIError(f"API request failed: {str(e)}")
    
    def get_transcript(self, video_url: str) -> str:
        """
        Get the transcript of a YouTube video.
        
        Args:
            video_url: URL of the YouTube video
            
        Returns:
            str: Video transcript or error message
            
        Raises:
            YouTubeError: If the video URL is invalid
            YouTubeAPIError: If the API request fails
        """
        try:
            video_id = extract_video_id(video_url)
            self.logger.info(f"Fetching transcript for video: {video_id}")
            
            data = self._make_api_request("video/subtitles", {"video_id": video_id})
            
            if "subtitles" not in data or not data["subtitles"]:
                self.logger.warning(f"No subtitles found for video: {video_id}")
                return "Aucune transcription disponible pour cette vidéo"
                
            transcript = format_transcript(data["subtitles"])
            
            self.logger.info(f"Successfully retrieved transcript ({len(transcript)} chars)")
            return transcript
            
        except YouTubeError as e:
            self.logger.error(f"YouTube error: {str(e)}")
            return f"Erreur: {str(e)}"
            
        except YouTubeAPIError as e:
            self.logger.error(f"API error: {str(e)}")
            return f"Erreur API: {str(e)}"
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return f"Erreur inattendue: {str(e)}" 