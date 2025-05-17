from typing import Optional
from app.tools.registry import register
from app.tools.media.core import (
    fetch_media_from_url,
    get_media_metadata,
    list_media,
    extract_text_from_image,
    extract_text_from_pdf,
    extract_audio_transcription,
    extract_video_audio
)
from app.tools.media.schema import MediaMetadata # Though not directly used in args, good for context
from app.utils.logging import get_logger
import os
import tempfile

logger = get_logger(__name__)

@register(name="load_media_from_url")
def load_media_from_url(url: str, session_id: Optional[str] = None) -> str:
    """
    Télécharge un média depuis une URL et le stocke pour traitement ultérieur.

    Args:
        url: URL du média à télécharger.
        session_id: ID de session optionnel pour associer le média.

    Returns:
        ID du média téléchargé ou message d'erreur.
    """
    metadata = fetch_media_from_url(url, session_id)
    if metadata:
        return f"Média téléchargé avec ID: {metadata.media_id}. Type: {metadata.media_type}"
    return "Erreur lors du téléchargement du média."

@register(name="list_available_media")
def list_available_media(session_id: Optional[str] = None) -> str:
    """
    Liste les médias actuellement disponibles, avec option de filtrage par session.

    Args:
        session_id: ID de session optionnel pour filtrer la liste.

    Returns:
        Liste formatée des médias disponibles ou message si aucun média.
    """
    media_items = list_media(session_id)
    if not media_items:
        return "Aucun média disponible" + (f" pour la session {session_id}." if session_id else ".")
    
    output = "Médias disponibles:\n"
    for m in media_items:
        output += f"  - ID: {m.media_id}, Type: {m.media_type}, URL: {m.original_url}, DL: {m.download_date.strftime("%Y-%m-%d %H:%M")}\n"
    return output

@register(name="extract_media_content")
def extract_media_content(media_id: str, max_pages: int = 10) -> str:
    """
    Extrait le contenu textuel ou transcrit d'un média précédemment chargé.

    Args:
        media_id: ID du média à traiter.
        max_pages: Nombre maximum de pages à extraire pour les PDF.

    Returns:
        Contenu extrait ou message d'erreur/d'information.
    """
    metadata = get_media_metadata(media_id)
    if not metadata:
        return f"Média avec ID '{media_id}' non trouvé."

    if metadata.processed and metadata.processed_content is not None:
        return f"[Contenu déjà traité pour {media_id}]\n{metadata.processed_content}"

    content = f"[Aucun contenu extractible ou type de média ({metadata.media_type}) non supporté pour l'extraction directe]"
    
    try:
        if metadata.media_type == "image":
            content = extract_text_from_image(metadata.local_path)
        elif metadata.media_type == "document":
            if metadata.content_type == "application/pdf":
                content = extract_text_from_pdf(metadata.local_path, max_pages)
            # Potentiellement ajouter d'autres types de documents (txt, docx) ici
            else:
                try: # Simple text file reading attempt
                    with open(metadata.local_path, 'r', encoding='utf-8') as f:
                        content = f"[Contenu textuel du fichier]\n\n{f.read()}"
                except Exception as e:
                    logger.warning(f"Impossible de lire le document texte {metadata.local_path} directement: {e}")
                    content = f"[Type de document ({metadata.content_type}) non directement extractible comme texte brut.]"

        elif metadata.media_type == "audio":
            content = extract_audio_transcription(metadata.local_path)
        elif metadata.media_type == "video":
            audio_path = extract_video_audio(metadata.local_path)
            if audio_path:
                content = extract_audio_transcription(audio_path)
                try:
                    os.remove(audio_path) # Nettoyer le fichier audio temporaire
                except Exception as e:
                    logger.error(f"Impossible de supprimer le fichier audio temporaire {audio_path}: {e}")
            else:
                content = "[Impossible d'extraire l'audio de la vidéo pour transcription.]"
        
        metadata.processed = True
        metadata.processed_content = content
        # Note: media_registry is updated in-place as MediaMetadata objects are mutable
        return content
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du contenu pour {media_id}: {e}", exc_info=True)
        return f"[Erreur majeure lors de l'extraction du contenu: {e}]" 