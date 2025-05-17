Ce document décrit la configuration et l’utilisation du module de calcul de dates relatives.

---

## Outils à ajouter dans les `Settings` et l’`.env`

Dans la section `ENABLED_TOOLS` (ou équivalent) de vos paramètres, ajoutez :
- `calculate_date_core`

---

## Prérequis

- Python 3.9+  
- Un fichier `.env` à la racine du projet (même si aucun paramètre spécifique n’est requis)  
- Dépendances installées :  
  ```bash
  pip3 install -r requirements.txt
````

---

## 1. Installation

Clonez le dépôt et installez les dépendances :

```bash
git clone <votre-repo>
cd <votre-repo>
pip3 install -r requirements.txt
```

---

## 2. Utilisation de la fonction `calculate_date_core`

La fonction `calculate_date_core` permet de calculer une date relative à aujourd’hui selon :

* **days** (`int`, options) : nombre de jours à ajouter (ou retrancher si négatif)
* **weeks** (`int`, options) : nombre de semaines à ajouter (ou retrancher si négatif)
* **weekday** (`int`, options) : jour de la semaine cible (0 = lundi … 6 = dimanche)
* **format\_str** (`str`, option) : format de sortie strftime (défaut `"%d/%m/%Y"`)

### Exemples

```python
from app.tools.date.core import calculate_date_core

# Date de demain
print(calculate_date_core(days=1))  
# → "18/05/2025" (si aujourd’hui est le 17/05/2025)

# Date dans 2 semaines et 3 jours
print(calculate_date_core(weeks=2, days=3, format_str="%Y-%m-%d"))  
# → "04-06-2025"

# Prochain mercredi (2)
print(calculate_date_core(weekday=2))  
# → "21/05/2025" (si aujourd’hui est le 17/05/2025)

# Date d’hier
print(calculate_date_core(days=-1))  
# → "16/05/2025"
```

---

## 3. Nettoyage

Une fois testé et intégré, vous pouvez supprimer en toute sécurité :

* `README.md` (exemple)
* `requirements.txt` (si vous gérez autrement vos dépendances)
* `.env.example`