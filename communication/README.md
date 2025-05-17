Ce document décrit la configuration et l’utilisation du module de logique métier pour l’envoi de messages WhatsApp et d’e-mails.

---

## Outils à ajouter dans les `Settings` et l’`.env`

Dans la section `ENABLED_TOOLS` ou équivalent de vos paramètres, ajoutez :
- `send_whatsapp_message`
- `send_whatsapp_to_chat`
- `retrieve_whatsapp_contact_id`
- `send_email`
- `retrieve_emails`

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

Cette section détaille les étapes précises pour récupérer vos identifiants SMTP/IMAP chez Hostinger et votre clé API (+ DSN) sur Unipile, afin de pouvoir les ajouter en toute sécurité dans votre fichier `.env`.

## Récupérer vos identifiants SMTP/IMAP chez Hostinger

Pour découvrir vos paramètres de messagerie chez Hostinger, commencez par vous connecter à votre compte et ouvrir le **hPanel**. Vous y accédez via « Emails » dans la barre latérale : les détails y sont centralisés dans la rubrique “Configuration Settings” de votre domaine ([Centre d'Aide Hostinger][1]).
Cliquez ensuite sur **Manage** (ou “Gérer”) à côté du nom de domaine concerné, puis sur **Connect Apps & Devices** ([Centre d'Aide Hostinger][2]). Dans la section **Manual Configuration**, déroulez pour afficher les valeurs suivantes :

* **SMTP (sortant)** :

  * Hôte : `smtp.hostinger.com`
  * Port : `465` (SSL/TLS) ou `587` (STARTTLS) ([Centre d'Aide Hostinger][2])
* **IMAP (entrant)** :

  * Hôte : `imap.hostinger.com`
  * Port : `993` (SSL) ([Centre d'Aide Hostinger][2])
* **POP3 (entrant)** :

  * Hôte : `pop.hostinger.com`
  * Port : `995` (SSL) ([Centre d'Aide Hostinger][2])

Si vous avez oublié le mot de passe du mailbox, rendez-vous dans **Emails › Mailboxes › Options › Change Password** pour le réinitialiser ([Centre d'Aide Hostinger][3]). Copiez ensuite votre identifiant (votre adresse e-mail complète) et le mot de passe choisi.

## Récupérer votre clé API et votre DSN sur Unipile

1. **Connexion au Dashboard**
   Ouvrez le [Unipile Dashboard](https://developer.unipile.com) et connectez-vous à votre espace administrateur ([unipile.com][4]).

2. **Génération et visualisation de la clé**
   Dans **API Usage** (ou **Access Tokens**), générez ou copiez votre **Access Token** : il s’agit de la valeur à utiliser dans l’en-tête `X-API-KEY` de vos requêtes ([Unipile][5]). Ne partagez jamais ce token publiquement.

3. **Récupération du DSN**
   Toujours sur la page d’accueil du Dashboard, repérez votre **Data Source Name (DSN)** : c’est l’URL de base de l’API Unipile (ex. `https://api8.unipile.com`) à utiliser dans vos appels ([unipile.com][6], [Unipile][7]).
   Pour les flux WhatsApp, ce même DSN est nécessaire en complément de votre clé : il est affiché en évidence sur la section “Messaging API” ([Unipile][8]).

4. **Test interactif**
   Vous pouvez vérifier immédiatement la validité de votre `X-API-KEY` et de votre DSN dans l’interface **API Reference** interactive du site Unipile : collez-les, sélectionnez une route (par ex. `GET /accounts`) et lancez l’appel ([Unipile][7]).

## Ajout dans votre `.env`

Enfin, éditez (ou créez) le fichier `.env` à la racine de votre projet :

```env
# Hostinger Email
EMAIL_USERNAME=votre_email@domaine.com
EMAIL_PASSWORD=votre_mot_de_passe

# Unipile Messaging API
UNIPILE_API_KEY=your_access_token
UNIPILE_DSN=https://api8.unipile.com

> **⚠️** Ne commitez jamais vos vraies clés dans le dépôt.

---

## 2. Paramètres dans `settings.py`

Assurez-vous que `app/utils/settings.py` lit bien ces variables :

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # WhatsApp
    api_keys: dict
    whatsapp: dict

    # Email
    email: dict

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
```

---

## 3. Utilisation du client WhatsApp

```python
from app.communication import get_whatsapp_client

client = get_whatsapp_client()

# Envoyer un nouveau message (recherche de contact + chat)
response = client.send_message(
    phone="+33612345678",
    text="Bonjour, ceci est un test WhatsApp !"
)
print(response)

# Envoyer un message dans un chat existant
response = client.send_message_to_existing_chat(
    chat_id="abcdef123456",
    text="Message dans un chat existant"
)
print(response)
```

Le décorateur `@with_retry()` gère automatiquement les tentatives en cas d’erreur réseau ou HTTP transitoire.

---

## 4. Utilisation du client Email

```python
from app.communication import get_email_client

email_client = get_email_client()

# Envoyer un email simple
result = email_client.send_email(
    to=["destinataire@example.com"],
    subject="Sujet du test",
    body="Contenu du message au format plain ou HTML"
)
print(result)

# Récupérer les 5 derniers e-mails non lus de la boîte INBOX
emails = email_client.retrieve_emails(
    folder="INBOX",
    limit=5,
    unread_only=True
)
for mail in emails:
    print(mail["subject"], mail["date"])
```

Le client Email supporte :

* Pièces jointes (liste de chemins de fichiers)
* CC / BCC
* Recherche IMAP et filtrage (`UNSEEN`, requête personnalisée)

---

## 5. Nettoyage

Une fois vos dépendances installées et vos clés enregistrées, vous pouvez supprimer en toute sécurité :

* `README.md` (exemple)
* `requirements.txt` (si vous utilisez un autre système de gestion)
* `.env.example`