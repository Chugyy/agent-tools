"""
Outils Langchain pour interagir avec Google Calendar.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.tools.registry import register
from app.utils.logging import get_logger
from app.utils.settings import get_settings # To access default calendar_id and timezone
from .core import (
    core_list_events,
    core_create_event,
    core_update_event,
    core_delete_event
)
from .schema import (
    ListEventsSchema,
    CreateEventSchema,
    UpdateEventSchema,
    DeleteEventSchema
)

logger = get_logger(__name__)
settings = get_settings()

def _format_datetime(dt_str: str) -> str:
    """Helper to format datetime strings for display."""
    if 'T' in dt_str: # Datetime string
        dt_obj = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt_obj.strftime('%d/%m/%Y %H:%M %Z')
    else: # Date string
        dt_obj = datetime.fromisoformat(dt_str)
        return dt_obj.strftime('%d/%m/%Y')

@register(name="lister_evenements_calendrier", args_schema=ListEventsSchema)
def lister_evenements_calendrier(count: int = 10, calendar_id: Optional[str] = None) -> str:
    """
    Récupère les N prochains événements du calendrier Google spécifié.

    Args:
        count: Nombre d'événements à récupérer (1-100).
        calendar_id: ID du calendrier (défaut: calendrier principal des settings).

    Returns:
        Liste formatée des événements ou message d'erreur/succès.
    """
    logger.info(f"Tool 'lister_evenements_calendrier' appelé avec count={count}, calendar_id={calendar_id}")
    try:
        events = core_list_events(count=count, calendar_id=calendar_id)
        if not events:
            return "Aucun événement à venir trouvé."
        
        output = f"Prochains événements ({len(events)}):\n"
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
            end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
            output += f"  - {event.get('summary', 'Sans titre')}\n"
            if start:
                output += f"    Début: {_format_datetime(start)}\n"
            if end:
                output += f"    Fin:   {_format_datetime(end)}\n"
            if event.get('location'):
                output += f"    Lieu:  {event.get('location')}\n"
            if event.get('description'):
                output += f"    Desc:  {event.get('description')[:50]}...\n"
            output += f"    ID:    {event.get('id')}\n\n"
        return output.strip()
    except Exception as e:
        logger.error(f"Erreur dans lister_evenements_calendrier: {e}", exc_info=True)
        return f"Erreur lors de la récupération des événements: {str(e)}"

@register(name="creer_evenement_calendrier", args_schema=CreateEventSchema)
def creer_evenement_calendrier(summary: str, start_time: str, end_time: str,
                             description: Optional[str] = None, location: Optional[str] = None,
                             attendees: Optional[List[str]] = None, calendar_id: Optional[str] = None) -> str:
    """
    Crée un nouvel événement dans le calendrier Google.

    Args:
        summary: Titre de l'événement.
        start_time: Date/heure de début (format ISO, ex: '2024-07-01T10:00:00').
        end_time: Date/heure de fin (format ISO, ex: '2024-07-01T11:00:00').
        description: Description de l'événement.
        location: Lieu de l'événement.
        attendees: Liste d'adresses e-mail des participants.
        calendar_id: ID du calendrier (défaut: calendrier principal des settings).

    Returns:
        Message de confirmation avec l'ID de l'événement ou message d'erreur.
    """
    logger.info(f"Tool 'creer_evenement_calendrier' appelé pour '{summary}'")
    try:
        # Validate and parse datetime strings to ensure they are in correct ISO format with timezone offset if needed
        # Google API expects RFC3339 format e.g., "2024-07-28T09:00:00-07:00" or with Z for UTC
        # For simplicity, assuming input `start_time` and `end_time` are correctly formatted or use a date parsing utility
        
        created_event = core_create_event(
            summary=summary, start_time=start_time, end_time=end_time,
            description=description, location=location, attendees=attendees,
            calendar_id=calendar_id
        )
        return f"Événement '{created_event.get('summary')}' créé avec succès. ID: {created_event.get('id')}"
    except Exception as e:
        logger.error(f"Erreur dans creer_evenement_calendrier: {e}", exc_info=True)
        return f"Erreur lors de la création de l'événement: {str(e)}"

@register(name="mettre_a_jour_evenement_calendrier", args_schema=UpdateEventSchema)
def mettre_a_jour_evenement_calendrier(event_id: str, calendar_id: Optional[str] = None,
                                   summary: Optional[str] = None, start_time: Optional[str] = None,
                                   end_time: Optional[str] = None, description: Optional[str] = None,
                                   location: Optional[str] = None, attendees: Optional[List[str]] = None) -> str:
    """
    Met à jour un événement existant dans le calendrier Google.
    Seuls les champs fournis seront mis à jour.

    Args:
        event_id: ID de l'événement à mettre à jour.
        calendar_id: ID du calendrier (défaut: calendrier principal des settings).
        summary: Nouveau titre.
        start_time: Nouvelle date/heure de début (format ISO).
        end_time: Nouvelle date/heure de fin (format ISO).
        description: Nouvelle description.
        location: Nouveau lieu.
        attendees: Nouvelle liste de participants (remplace l'existante).

    Returns:
        Message de confirmation ou message d'erreur.
    """
    logger.info(f"Tool 'mettre_a_jour_evenement_calendrier' appelé pour event_id: {event_id}")
    updates = {
        k: v for k, v in {
            'summary': summary, 'start_time': start_time, 'end_time': end_time,
            'description': description, 'location': location, 'attendees': attendees
        }.items() if v is not None
    }
    if not updates:
        return "Aucune information de mise à jour fournie."

    try:
        updated_event = core_update_event(event_id=event_id, calendar_id=calendar_id, updates=updates)
        return f"Événement '{updated_event.get('summary')}' (ID: {event_id}) mis à jour avec succès."
    except ValueError as ve: # Specific error from core_update_event if event not found
        return str(ve)
    except Exception as e:
        logger.error(f"Erreur dans mettre_a_jour_evenement_calendrier: {e}", exc_info=True)
        return f"Erreur lors de la mise à jour de l'événement {event_id}: {str(e)}"

@register(name="supprimer_evenement_calendrier", args_schema=DeleteEventSchema)
def supprimer_evenement_calendrier(event_id: str, calendar_id: Optional[str] = None) -> str:
    """
    Supprime un événement du calendrier Google.

    Args:
        event_id: ID de l'événement à supprimer.
        calendar_id: ID du calendrier (défaut: calendrier principal des settings).

    Returns:
        Message de confirmation ou message d'erreur.
    """
    logger.info(f"Tool 'supprimer_evenement_calendrier' appelé pour event_id: {event_id}")
    try:
        success = core_delete_event(event_id=event_id, calendar_id=calendar_id)
        if success:
            return f"Événement {event_id} supprimé avec succès."
        else:
            # This case might occur if core_delete_event returns False for a 404, adjust as needed.
            return f"Événement {event_id} non trouvé ou déjà supprimé."
    except Exception as e:
        logger.error(f"Erreur dans supprimer_evenement_calendrier: {e}", exc_info=True)
        return f"Erreur lors de la suppression de l'événement {event_id}: {str(e)}" 