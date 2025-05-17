"""
Outils Langchain pour la communication (WhatsApp, Email).
"""
from typing import Optional, List

from app.tools.registry import register
from app.utils.logging import get_logger
from app.utils.settings import get_settings
from .core import (
    get_whatsapp_client,
    format_phone_number,
    get_email_client
)
from .schema import (
    WhatsAppSendMessageSchema,
    WhatsAppReplyToChatSchema,
    EmailSendSchema,
    EmailRetrieveSchema
)

logger = get_logger(__name__)
settings = get_settings() # Used for default account_id and error messages

@register(name="envoyer_message_whatsapp", args_schema=WhatsAppSendMessageSchema)
def envoyer_message_whatsapp(phone_number: str, message: str, account_id: Optional[str] = None) -> str:
    """
    Envoie un message WhatsApp à un numéro de téléphone spécifié.

    Args:
        phone_number: Numéro de téléphone du destinataire (format international recommandé).
        message: Contenu du message à envoyer.
        account_id: (Optionnel) ID du compte WhatsApp à utiliser si différent de celui par défaut.

    Returns:
        Message de confirmation ou d'erreur.
    """
    logger.info(f"Tool 'envoyer_message_whatsapp' appelé pour {phone_number}")
    if not settings.whatsapp.account_id and not account_id:
        return "Erreur: Aucun ID de compte WhatsApp configuré par défaut ou fourni."
    if not phone_number or not message:
        return "Erreur: Le numéro de téléphone et le message sont requis."

    cleaned_phone = format_phone_number(phone_number)
    if not cleaned_phone or len(cleaned_phone) < 8:
        return f"Erreur: Numéro de téléphone '{phone_number}' invalide après formatage: '{cleaned_phone}'."

    # Use provided account_id or default from settings
    # Note: The UniPileWhatsAppClient in core.py uses settings.whatsapp.account_id directly.
    # If a per-call account_id is needed, the client or core function needs adjustment.
    # For now, this tool relies on the globally configured account_id.

    try:
        client = get_whatsapp_client()
        result = client.send_message(cleaned_phone, message)
        chat_id = result.get("chat_id")
        if chat_id:
            return f"Message WhatsApp envoyé à {cleaned_phone}. ID du Chat: {chat_id}"
        return "Message WhatsApp envoyé, mais aucun ID de chat retourné."
    except ValueError as ve: # Configuration error from get_whatsapp_client
        logger.error(f"Erreur de configuration WhatsApp: {ve}")
        return f"Erreur de configuration WhatsApp: {ve}"
    except Exception as e:
        logger.error(f"Erreur envoi WhatsApp à {cleaned_phone}: {e}", exc_info=True)
        return f"Erreur lors de l'envoi du message WhatsApp: {str(e)}"

@register(name="repondre_chat_whatsapp", args_schema=WhatsAppReplyToChatSchema)
def repondre_chat_whatsapp(chat_id: str, message: str) -> str:
    """
    Répond à un message dans un chat WhatsApp existant.

    Args:
        chat_id: ID du chat WhatsApp auquel répondre.
        message: Contenu du message à envoyer.

    Returns:
        Message de confirmation ou d'erreur.
    """
    logger.info(f"Tool 'repondre_chat_whatsapp' appelé pour chat ID: {chat_id}")
    if not settings.whatsapp.account_id:
         return "Erreur: Aucun ID de compte WhatsApp configuré par défaut."
    if not chat_id or not message:
        return "Erreur: L'ID du chat et le message sont requis."
    
    try:
        client = get_whatsapp_client()
        result = client.send_message_to_existing_chat(chat_id, message)
        msg_id = result.get("id")
        if msg_id:
            return f"Réponse envoyée au chat WhatsApp {chat_id}. ID du Message: {msg_id}"
        return "Réponse WhatsApp envoyée, mais aucun ID de message retourné."
    except ValueError as ve: # Configuration error
        logger.error(f"Erreur de configuration WhatsApp: {ve}")
        return f"Erreur de configuration WhatsApp: {ve}"
    except Exception as e:
        logger.error(f"Erreur réponse WhatsApp au chat {chat_id}: {e}", exc_info=True)
        return f"Erreur lors de la réponse au chat WhatsApp: {str(e)}"

@register(name="envoyer_email", args_schema=EmailSendSchema)
def envoyer_email(to: List[str], subject: str, body: str,
                  cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None,
                  attachments: Optional[List[str]] = None) -> str:
    """
    Envoie un email en utilisant SMTP.

    Args:
        to: Liste des adresses email des destinataires principaux.
        subject: Sujet de l'email.
        body: Corps du message. Peut être du texte brut ou HTML.
        cc: (Optionnel) Liste des adresses email en copie carbone (CC).
        bcc: (Optionnel) Liste des adresses email en copie carbone invisible (BCC).
        attachments: (Optionnel) Liste des chemins absolus des fichiers à joindre.

    Returns:
        Message de confirmation ou d'erreur.
    """
    logger.info(f"Tool 'envoyer_email' appelé pour sujet: {subject}")
    if not to:
        return "Erreur: Au moins un destinataire (to) est requis."
    if not subject or not body:
        return "Erreur: Le sujet et le corps du message sont requis."

    try:
        client = get_email_client()
        result = client.send_email(to, subject, body, cc, bcc, attachments)
        if result["success"]:
            attach_info = f" avec {result['attachment_count']} pièce(s) jointe(s)" if result['attachment_count'] > 0 else ""
            return f"Email envoyé à {len(result['to'] + result['cc'] + result['bcc'])} destinataire(s){attach_info}. Sujet: {subject}"
        return f"Échec de l'envoi de l'email: {result.get('error', 'Erreur inconnue')}"
    except ValueError as ve: # Configuration error
        logger.error(f"Erreur de configuration Email: {ve}")
        return f"Erreur de configuration Email: {ve}"
    except Exception as e:
        logger.error(f"Erreur envoi email: {e}", exc_info=True)
        return f"Erreur lors de l'envoi de l'email: {str(e)}"

@register(name="recuperer_emails", args_schema=EmailRetrieveSchema)
def recuperer_emails(folder: str = "INBOX", limit: int = 10, 
                     unread_only: bool = False, search_query: Optional[str] = None) -> str:
    """
    Récupère les emails d'un compte en utilisant IMAP.

    Args:
        folder: Dossier IMAP à consulter (ex: "INBOX", "Sent", "Spam").
        limit: Nombre maximum d'emails à récupérer.
        unread_only: Si True, ne récupère que les emails non lus.
        search_query: Critères de recherche IMAP avancés (ex: 'FROM "foo@example.com" SINCE 01-Jan-2023').

    Returns:
        Liste formatée des emails trouvés ou message d'erreur/information.
    """
    logger.info(f"Tool 'recuperer_emails' appelé pour dossier: {folder}, limite: {limit}")
    try:
        client = get_email_client()
        emails = client.retrieve_emails(folder, limit, unread_only, search_query)
        if not emails:
            return f"Aucun email trouvé dans le dossier '{folder}' avec les critères spécifiés."
        
        output = f"Emails récupérés de '{folder}' ({len(emails)}):\n\n"
        for i, mail in enumerate(emails, 1):
            output += f"--- Email {i} ---\n"
            output += f"ID: {mail.get('id')}\n"
            output += f"De: {mail.get('from', 'N/A')}\n"
            output += f"À: {mail.get('to', 'N/A')}\n"
            if mail.get('cc'): output += f"Cc: {mail.get('cc')}\n"
            output += f"Sujet: {mail.get('subject', '(Pas de sujet)')}\n"
            output += f"Date: {mail.get('date', 'N/A')}\n"
            if mail.get('has_attachments') and mail.get('attachments'):
                output += f"Pièces jointes: {", ".join(mail['attachments'])}\n"
            
            body_preview = mail.get('body', '')[:250]
            if len(mail.get('body', '')) > 250: body_preview += "..."
            output += f"Extrait du corps:\n{body_preview}\n\n"
        return output.strip()
    except ValueError as ve: # Configuration error
        logger.error(f"Erreur de configuration Email: {ve}")
        return f"Erreur de configuration Email: {ve}"
    except Exception as e:
        logger.error(f"Erreur récupération emails: {e}", exc_info=True)
        return f"Erreur lors de la récupération des emails: {str(e)}" 