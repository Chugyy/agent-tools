from typing import Optional
from pydantic import BaseModel, Field

class DateCalculationSchema(BaseModel):
    """Schéma pour le calcul de dates."""
    days: Optional[int] = Field(0, description="Nombre de jours à ajouter/soustraire à aujourd'hui. Utilisé si 'weekday' n'est pas spécifié ou si 'days' et 'weeks' sont non nuls.")
    weeks: Optional[int] = Field(0, description="Nombre de semaines à ajouter/soustraire à aujourd'hui. Utilisé si 'weekday' n'est pas spécifié ou si 'days' et 'weeks' sont non nuls.")
    weekday: Optional[int] = Field(None, description="Jour de la semaine à trouver (0=lundi, 6=dimanche). Si spécifié et non None, ce paramètre prend le dessus sur 'days' et 'weeks' (sauf si 'days' ou 'weeks' sont non-nuls, auquel cas ils sont prioritaires). Pour trouver le prochain jour spécifié, laissez 'days' et 'weeks' à 0 ou non spécifiés.")
    format: Optional[str] = Field("%d/%m/%Y", description="Format de date désiré") 