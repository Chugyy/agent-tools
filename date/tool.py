from typing import Optional
from app.tools.registry import register
from app.tools.date.schema import DateCalculationSchema
from app.tools.date.core import calculate_date_core
from app.utils.logging import get_logger

logger = get_logger(__name__)

@register(name="calculer_date", args_schema=DateCalculationSchema)
def calculer_date(
    days: Optional[int] = 0,
    weeks: Optional[int] = 0,
    weekday: Optional[int] = None,
    format: Optional[str] = "%d/%m/%Y" # Schema uses 'format', tool func keeps 'format'
) -> str:
    """
    Calcule une date relative à aujourd'hui.
    NOTE: Si 'days' ou 'weeks' sont fournis avec une valeur non nulle, ils prennent priorité sur 'weekday'.
    Pour trouver un 'weekday' spécifique (ex: prochain lundi), assurez-vous que 'days' et 'weeks' sont à 0 ou non fournis.
    Retourne la date au format spécifié (par défaut %d/%m/%Y).
    
    Args:
        days: Nombre de jours à ajouter (positif) ou soustraire (négatif). Prioritaire sur 'weekday' si non nul.
        weeks: Nombre de semaines à ajouter (positif) ou soustraire (négatif). Prioritaire sur 'weekday' si non nul.
        weekday: Jour de la semaine à trouver (0=lundi, 1=mardi, ..., 6=dimanche). Utilisé si 'days' et 'weeks' sont nuls ou non fournis.
        format: Format de la date retournée (%d/%m/%Y par défaut)
        
    Returns:
        Date calculée au format demandé.
        
    Exemples:
        calculer_date() -> "16/05/2025" (si aujourd'hui est le 16 Mai 2025)
        calculer_date(days=1) -> "17/05/2025"
        calculer_date(days=-1) -> "15/05/2025"
        calculer_date(weeks=1) -> "23/05/2025"
        calculer_date(weekday=0) -> "19/05/2025" (si le prochain lundi est le 19 Mai 2025)
    """
    logger.debug(f"Calculer_date appelé avec days={days}, weeks={weeks}, weekday={weekday}, format={format}")
    return calculate_date_core(days=days, weeks=weeks, weekday=weekday, format_str=format) 