"""
Logique métier pour l'intégration avec Google Calendar.
"""
import os
import json
import functools
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.settings import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

SCOPES_READ_ONLY = ['https://www.googleapis.com/auth/calendar.readonly']
SCOPES_FULL_ACCESS = ['https://www.googleapis.com/auth/calendar']

# Adjusted paths to be relative to the app's root or a configurable base path
TOKEN_PATH = os.path.join(settings.base_dir, settings.calendar.token_file)
CREDENTIALS_PATH = os.path.join(settings.base_dir, settings.calendar.credentials_file)

def with_retry(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    status_code = e.resp.status if hasattr(e, 'resp') else 0
                    if status_code in (400, 401, 403, 404):
                        logger.error(f"Erreur HTTP {status_code} non réessayable: {e}")
                        raise
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Échec après {max_retries} tentatives - Erreur HTTP {status_code}: {e}")
                        raise
                    logger.warning(f"Tentative {retries}/{max_retries} échouée - Erreur HTTP {status_code}: {e}")
                    time.sleep(delay * (2 ** (retries - 1)))
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Échec après {max_retries} tentatives: {e}")
                        raise
                    logger.warning(f"Tentative {retries}/{max_retries} échouée: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

def get_credentials(read_only: bool = None) -> Credentials:
    if read_only is None:
        read_only = settings.calendar.scopes_read_only
    scopes = SCOPES_READ_ONLY if read_only else SCOPES_FULL_ACCESS
    creds = None

    token_dir = os.path.dirname(TOKEN_PATH)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir, exist_ok=True)
        logger.info(f"Création du répertoire pour le token: {token_dir}")

    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, 'r') as token_file:
                creds_data = json.load(token_file)
            creds = Credentials.from_authorized_user_info(creds_data, scopes)
            logger.debug("Token chargé depuis le fichier")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du token depuis {TOKEN_PATH}: {e}")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.debug("Token rafraîchi avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du rafraîchissement du token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                logger.error(f"Fichier de credentials introuvable: {CREDENTIALS_PATH}")
                raise FileNotFoundError(
                    f"Fichier de credentials introuvable. Placez {settings.calendar.credentials_file} "
                    f"dans {os.path.dirname(CREDENTIALS_PATH)}."
                )
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, scopes)
                # Utiliser run_console pour éviter le besoin d'un serveur local si l'app est headless
                creds = flow.run_console()
                logger.info("Nouvelles autorisations obtenues via la console")
            except Exception as e:
                logger.error(f"Erreur lors de l'authentification OAuth: {e}")
                raise
        
        try:
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
            logger.debug(f"Token sauvegardé dans {TOKEN_PATH}")
        except Exception as e:
            logger.warning(f"Impossible de sauvegarder le token dans {TOKEN_PATH}: {e}")
    
    return creds

def get_calendar_service(read_only: bool = None) -> Any:
    try:
        creds = get_credentials(read_only=read_only)
        service = build('calendar', 'v3', credentials=creds, cache_discovery=False) # Disable cache for server environments
        return service
    except Exception as e:
        logger.error(f"Erreur lors de la création du service Calendar: {e}")
        raise

# --- Core Logic Functions (called by tools) ---

@with_retry()
def core_list_events(count: int, calendar_id: Optional[str]) -> List[Dict[str, Any]]:
    effective_calendar_id = calendar_id or settings.calendar.calendar_id
    logger.info(f"Récupération de {count} événements du calendrier {effective_calendar_id}")
    service = get_calendar_service(read_only=True)
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=effective_calendar_id, timeMin=now,
        maxResults=count, singleEvents=True, orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

@with_retry()
def core_create_event(summary: str, start_time: str, end_time: str,
                      description: Optional[str], location: Optional[str],
                      attendees: Optional[List[str]], calendar_id: Optional[str]) -> Dict[str, Any]:
    effective_calendar_id = calendar_id or settings.calendar.calendar_id
    service = get_calendar_service(read_only=False)
    event_body = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': settings.calendar.timezone},
        'end': {'dateTime': end_time, 'timeZone': settings.calendar.timezone},
        'attendees': [{'email': email} for email in attendees] if attendees else []
    }
    created_event = service.events().insert(calendarId=effective_calendar_id, body=event_body).execute()
    logger.info(f"Événement créé: {created_event.get('id')} dans {effective_calendar_id}")
    return created_event

@with_retry()
def core_update_event(event_id: str, calendar_id: Optional[str],
                      updates: Dict[str, Any]) -> Dict[str, Any]:
    effective_calendar_id = calendar_id or settings.calendar.calendar_id
    service = get_calendar_service(read_only=False)
    
    # Fetch the existing event first to ensure it exists
    try:
        existing_event = service.events().get(calendarId=effective_calendar_id, eventId=event_id).execute()
    except HttpError as e:
        if e.resp.status == 404:
            logger.error(f"Événement {event_id} non trouvé dans {effective_calendar_id} pour mise à jour.")
            raise ValueError(f"Événement {event_id} non trouvé.")
        raise

    event_body = {}
    if 'summary' in updates: event_body['summary'] = updates['summary']
    if 'description' in updates: event_body['description'] = updates['description']
    if 'location' in updates: event_body['location'] = updates['location']
    if 'start_time' in updates: event_body['start'] = {'dateTime': updates['start_time'], 'timeZone': settings.calendar.timezone}
    if 'end_time' in updates: event_body['end'] = {'dateTime': updates['end_time'], 'timeZone': settings.calendar.timezone}
    if 'attendees' in updates and updates['attendees'] is not None:
        event_body['attendees'] = [{'email': email} for email in updates['attendees']]
    
    if not event_body:
        logger.info(f"Aucune mise à jour fournie pour l'événement {event_id}")
        return existing_event # Return existing if no actual changes are made

    updated_event = service.events().patch(calendarId=effective_calendar_id, eventId=event_id, body=event_body).execute()
    logger.info(f"Événement {event_id} mis à jour dans {effective_calendar_id}")
    return updated_event

@with_retry()
def core_delete_event(event_id: str, calendar_id: Optional[str]) -> bool:
    effective_calendar_id = calendar_id or settings.calendar.calendar_id
    service = get_calendar_service(read_only=False)
    try:
        service.events().delete(calendarId=effective_calendar_id, eventId=event_id).execute()
        logger.info(f"Événement {event_id} supprimé de {effective_calendar_id}")
        return True
    except HttpError as e:
        if e.resp.status == 404:
            logger.warning(f"Tentative de suppression d'un événement inexistant: {event_id} dans {effective_calendar_id}")
            return False # Or raise an error, depending on desired behavior
        logger.error(f"Erreur HTTP lors de la suppression de l'événement {event_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la suppression de l'événement {event_id}: {e}")
        raise 