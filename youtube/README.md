Ce document décrit la configuration et l’utilisation du module de transcription YouTube via l’API RapidAPI.

---

## Outils à ajouter dans les `Settings` et l’`.env`

Dans la section `ENABLED_TOOLS` (ou équivalent) de vos paramètres, ajoutez :
- `get_youtube_transcript`

---

## Prérequis

- Python 3.9+  
- Un fichier `.env` à la racine du projet  
- Dépendances installées :  
  ```bash
  pip3 install -r requirements.txt
````

---

## 1. Configuration des variables d’environnement

Créez ou mettez à jour votre fichier `.env` avec la clé RapidAPI :

```env
# RapidAPI YouTube
RAPIDAPI_KEY=your_rapidapi_key_here
```

> **⚠️** Ne commitez jamais vos vraies clés dans le dépôt.

---

## 2. Paramètres dans `settings.py`

Assurez-vous que `app/utils/settings.py` charge bien la clé RapidAPI :

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    api_keys: dict  # doit contenir { "rapid_api": "<clé>" }

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
```

---

## 3. Utilisation de la classe YouTubeCore

```python
from app.youtube.core import YouTubeCore

# Instanciation
yt = YouTubeCore()

# Récupérer la transcription d’une vidéo YouTube
video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
transcript = yt.get_transcript(video_url)

print(transcript)
```

* La méthode `get_transcript(video_url)` :

  * Extrait l’ID de la vidéo
  * Appelle l’endpoint `video/subtitles`
  * Formate et renvoie le texte de la transcription
  * En cas d’erreur, renvoie un message descriptif

---

## 4. Nettoyage

Une fois vos dépendances installées et vos clés configurées, vous pouvez supprimer en toute sécurité :

* `README.md` (exemple)
* `requirements.txt` (si vous utilisez un autre gestionnaire)
* `.env.example`