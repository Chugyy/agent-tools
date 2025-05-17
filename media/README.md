Ce document décrit la configuration et l’utilisation du module de gestion et d’extraction de médias.

---

## Outils à ajouter dans les `Settings` et l’`.env`

Dans la section `ENABLED_TOOLS` (ou équivalent) de vos paramètres, ajoutez :
- `fetch_media_from_url`
- `get_media_metadata`
- `list_media`
- `cleanup_old_media`
- `extract_text_from_image`
- `extract_text_from_pdf`
- `extract_audio_transcription`
- `extract_video_audio`

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

Créez ou mettez à jour votre fichier `.env` avec votre clé OpenAI :

```env
# OpenAI pour la transcription audio
OPENAI_API_KEY=your_openai_api_key_here
```

> **⚠️** Ne commitez jamais vos vraies clés dans le dépôt.

---

## 2. Paramètres dans `settings.py`

Assurez-vous que `app/utils/settings.py` charge bien la clé OpenAI :

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    api_keys: dict  # doit contenir { "openai": "<clé>" }
    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
```

---

## 3. Fonctionnalités principales

Le module fournit :

* **Mise en cache des médias** dans `media_cache/`
* **fetch\_media\_from\_url(url, session\_id=None)**
  Télécharge un média, le stocke en cache et renvoie un objet `MediaMetadata`.
* **get\_media\_metadata(media\_id)**
  Récupère les métadonnées d’un média déjà téléchargé.
* **list\_media(session\_id=None)**
  Liste tous les médias (optionnellement filtrés par `session_id`).
* **cleanup\_old\_media(max\_age\_hours=24)**
  Supprime les fichiers plus anciens que `max_age_hours`.

### Extraction de contenu

* **extract\_text\_from\_image(file\_path)**
  OCR via `pytesseract` et `Pillow`.
* **extract\_text\_from\_pdf(file\_path, max\_pages=10)**
  Extraction textuelle via `PyMuPDF` (fitz).
* **extract\_audio\_transcription(file\_path, model="whisper-1")**
  Transcription audio avec l’API OpenAI.
* **extract\_video\_audio(file\_path)**
  Extraction de la piste audio d’une vidéo via `moviepy`.

---

## 4. Exemples d’utilisation

```python
from app.tools.media.core import (
    fetch_media_from_url,
    get_media_metadata,
    list_media,
    cleanup_old_media,
    extract_text_from_image,
    extract_text_from_pdf,
    extract_audio_transcription,
    extract_video_audio
)

# 1. Télécharger et mettre en cache un média
meta = fetch_media_from_url("https://example.com/image.jpg", session_id="sess1")
print(meta.media_id, meta.local_path)

# 2. Récupérer les métadonnées
info = get_media_metadata(meta.media_id)
print(info)

# 3. Lister tous les médias de la session
all_media = list_media("sess1")
print([m.media_id for m in all_media])

# 4. Nettoyer les anciens médias (>24 h)
deleted_count = cleanup_old_media(max_age_hours=24)
print(f"{deleted_count} fichiers supprimés")

# 5. Extraire du texte d’une image
ocr_text = extract_text_from_image(meta.local_path)
print(ocr_text)

# 6. Extraire du texte d’un PDF
pdf_text = extract_text_from_pdf("/path/to/doc.pdf")
print(pdf_text)

# 7. Transcription audio
transcript = extract_audio_transcription("/path/to/audio.mp3")
print(transcript)

# 8. Extraction audio d’une vidéo
audio_path = extract_video_audio("/path/to/video.mp4")
print("Audio extrait →", audio_path)
```

---

## 5. Nettoyage

Une fois vos dépendances installées et vos clés configurées, vous pouvez supprimer en toute sécurité :

* `README.md` (exemple)
* `requirements.txt` (si vous utilisez un autre gestionnaire)
* `.env.example`