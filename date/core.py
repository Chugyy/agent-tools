import datetime
from typing import Optional
from app.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_date_core(
    days: Optional[int] = 0,
    weeks: Optional[int] = 0,
    weekday: Optional[int] = None,
    format_str: Optional[str] = "%d/%m/%Y" # Renamed to avoid conflict with built-in format
) -> str:
    """
    Logique principale pour calculer une date relative à aujourd'hui.
    """
    today = datetime.datetime.now()
    
    jour_semaine = {
        0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi",
        4: "vendredi", 5: "samedi", 6: "dimanche"
    }
    
    description = "aujourd'hui"
    new_date = today

    if days != 0 or weeks != 0:
        delta = datetime.timedelta(days=days + (weeks*7) if weeks is not None else days)
        new_date = today + delta
        
        if days == 1 and weeks == 0:
            description = "demain"
        elif days == -1 and weeks == 0:
            description = "hier"
        elif days == 2 and weeks == 0:
            description = "après-demain"
        elif days == -2 and weeks == 0:
            description = "avant-hier"
        elif weeks == 1 and days == 0:
            description = "dans une semaine"
        elif weeks == -1 and days == 0:
            description = "il y a une semaine"
        else:
            parts = []
            if weeks is not None and weeks != 0:
                parts.append(f"{abs(weeks)} semaine{'s' if abs(weeks) > 1 else ''}")
            if days is not None and days != 0:
                parts.append(f"{abs(days)} jour{'s' if abs(days) > 1 else ''}")
            
            if not parts: # Should not happen if days !=0 or weeks != 0
                 description = "aujourd'hui"
            elif (weeks or 0) > 0 or (days or 0) > 0:
                description = f"dans {' et '.join(parts)}"
            else: # negative offset
                description = f"il y a {' et '.join(parts)}"
            
    elif weekday is not None:
        if not (0 <= weekday <= 6):
            return f"Erreur: weekday ({weekday}) doit être entre 0 (lundi) et 6 (dimanche)."
            
        current_weekday = today.weekday()
        days_ahead = weekday - current_weekday
        
        if days_ahead <= 0: # If it's today or already passed this week
            days_ahead += 7 # Move to next week
            
        new_date = today + datetime.timedelta(days=days_ahead)
        description = f"prochain {jour_semaine[weekday]}"
        
    else:
        new_date = today
        description = "aujourd'hui"
    
    formatted_date = new_date.strftime(format_str)
    jour = jour_semaine[new_date.weekday()]
    
    # Ajuster la formulation pour "prochain lundi"
    # if weekday is not None and (days == 0 and weeks == 0):
    #      return f"Le {description} ({jour}) sera le {formatted_date}"
    # elif description == "aujourd'hui":
    #     return f"Aujourd'hui ({jour}) nous sommes le {formatted_date}"
    # else:
    #     return f"La date {description} ({jour}) est le {formatted_date}"
    return formatted_date 