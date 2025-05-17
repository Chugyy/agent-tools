import os
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse
import mimetypes
import tempfile
import hashlib
from io import BytesIO
import openai # Keep openai import if transcription/other OpenAI features are used directly

from app.tools.media.schema import MediaMetadata # Import MediaMetadata
from app.utils.settings import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Configuration
MEDIA_CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../media_cache")) # Adjusted path
os.makedirs(MEDIA_CACHE_DIR, exist_ok=True)

# Types de médias supportés
SUPPORTED_MIME_TYPES = {
    "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
    "document": ["application/pdf", "text/plain", "text/csv", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "audio": ["audio/mpeg", "audio/wav", "audio/ogg"],
    "video": ["video/mp4", "video/mpeg", "video/webm"]
}

# Registre des médias en mémoire
media_registry: Dict[str, MediaMetadata] = {}

def url_to_media_type(url: str, content_type: Optional[str] = None) -> str:
    if content_type:
        for media_type, mime_types in SUPPORTED_MIME_TYPES.items():
            if any(content_type.startswith(mime) for mime in mime_types):
                return media_type
    
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return "image"
    elif ext in ['.pdf', '.txt', '.doc', '.docx']:
        return "document"
    elif ext in ['.mp3', '.wav', '.ogg']:
        return "audio"
    elif ext in ['.mp4', '.mpeg', '.webm']:
        return "video"
    
    return "document"

def fetch_media_from_url(url: str, session_id: Optional[str] = None) -> Optional[MediaMetadata]:
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            logger.error(f"URL invalide: {url}")
            return None
            
        url_hash = hashlib.md5(url.encode()).hexdigest()
        media_id = str(uuid.uuid4())
        
        logger.info(f"Téléchargement du média depuis {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        media_type = url_to_media_type(url, content_type)
        
        ext = mimetypes.guess_extension(content_type) or os.path.splitext(parsed_url.path)[1]
        if not ext:
            ext = ".bin"
            
        filename = f"{url_hash}{ext}"
        file_path = os.path.join(MEDIA_CACHE_DIR, filename)
        
        content = response.content
        with open(file_path, "wb") as f:
            f.write(content)
            
        size = len(content)
        
        metadata = MediaMetadata(
            media_id=media_id,
            original_url=url,
            local_path=file_path,
            media_type=media_type,
            content_type=content_type,
            size=size,
            session_id=session_id
        )
        
        media_registry[media_id] = metadata
        
        logger.info(f"Média téléchargé avec succès: {media_id} ({media_type}, {size} octets)")
        return metadata
        
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du média {url}: {str(e)}", exc_info=True)
        return None

def get_media_metadata(media_id: str) -> Optional[MediaMetadata]:
    return media_registry.get(media_id)

def list_media(session_id: Optional[str] = None) -> List[MediaMetadata]:
    if session_id:
        return [m for m in media_registry.values() if m.session_id == session_id]
    return list(media_registry.values())

def cleanup_old_media(max_age_hours: int = 24) -> int:
    now = datetime.now()
    to_delete = []
    
    for media_id, metadata in media_registry.items():
        age = (now - metadata.download_date).total_seconds() / 3600
        if age > max_age_hours:
            to_delete.append(media_id)
    
    count = 0
    for media_id in to_delete:
        metadata = media_registry[media_id]
        try:
            if os.path.exists(metadata.local_path):
                os.remove(metadata.local_path)
            del media_registry[media_id]
            count += 1
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du média {media_id}: {str(e)}")
    
    return count

# ===== Fonctions d'extraction de contenu =====

def extract_text_from_image(file_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        
        if not text.strip():
            return "[Aucun texte détecté dans l'image]"
            
        return f"[Texte extrait de l'image]\n\n{text}"
    except ImportError:
        return "[Extraction d'OCR impossible: pytesseract n'est pas installé]"
    except Exception as e:
        logger.error(f"Erreur OCR pour {file_path}: {e}")
        return f"[Erreur OCR: {e}]"

def extract_text_from_pdf(file_path: str, max_pages: int = 10) -> str:
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(file_path)
        text = []
        num_pages_to_extract = min(len(doc), max_pages)

        for page_num in range(num_pages_to_extract):
            page = doc.load_page(page_num)
            text.append(page.get_text("text"))
        
        doc.close()
        
        if not any(t.strip() for t in text):
            return "[Aucun texte détecté dans le PDF]"

        full_text = "\n".join(text)
        if len(doc) > max_pages:
             full_text += f"\n\n[Contenu tronqué après {max_pages} pages sur {len(doc)}]"
        
        return f"[Texte extrait du PDF]\n\n{full_text}"
    except ImportError:
        return "[Extraction PDF impossible: PyMuPDF (fitz) n'est pas installé]"
    except Exception as e:
        logger.error(f"Erreur extraction PDF {file_path}: {e}")
        return f"[Erreur extraction PDF: {e}]"

def extract_audio_transcription(file_path: str, model: str = "whisper-1") -> str:
    if not settings.api_keys.openai:
        logger.warning("Clé API OpenAI non configurée. Transcription audio désactivée.")
        return "[Transcription audio impossible: clé API OpenAI manquante]"
    try:
        client = openai.OpenAI(api_key=settings.api_keys.openai)
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
        return f"[Transcription audio]\n\n{transcript.text}"
    except openai.APIError as e:
        logger.error(f"Erreur API OpenAI (transcription) pour {file_path}: {e}")
        return f"[Erreur API OpenAI (transcription): {e}]"
    except Exception as e:
        logger.error(f"Erreur de transcription audio pour {file_path}: {e}")
        return f"[Erreur de transcription: {e}]"


def extract_video_audio(file_path: str) -> Optional[str]:
    try:
        from moviepy.editor import VideoFileClip

        video_clip = VideoFileClip(file_path)
        audio_path = tempfile.mktemp(suffix=".mp3", dir=MEDIA_CACHE_DIR)
        video_clip.audio.write_audiofile(audio_path, logger=None) # Disable moviepy logger
        video_clip.close()
        return audio_path
    except ImportError:
        logger.warning("MoviePy non installé. Impossible d'extraire l'audio de la vidéo.")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de l'audio de la vidéo {file_path}: {e}")
        return None 