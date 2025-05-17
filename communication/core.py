"""
Logique métier pour les outils de communication (WhatsApp, Email).
"""
import requests
import functools
import time
import smtplib
import imaplib
import email
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import decode_header
from email.utils import formataddr
from datetime import datetime, timezone # Python 3.9+ can use ZoneInfo
from typing import Optional, Dict, Any, List

from app.utils.settings import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

def with_retry(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as e:
                    status_code = e.response.status_code if hasattr(e, 'response') else 0
                    if status_code in (400, 401, 403, 422):
                        logger.error(f"Erreur HTTP {status_code} non réessayable: {e}")
                        raise
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Échec après {max_retries} tentatives - Erreur HTTP {status_code}: {e}")
                        raise
                    logger.warning(f"Tentative {retries}/{max_retries} échouée - Erreur HTTP {status_code}: {e}")
                    time.sleep(delay * (2 ** (retries - 1)))
                except (requests.ConnectionError, requests.Timeout) as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Échec après {max_retries} tentatives - Erreur de connexion: {e}")
                        raise
                    logger.warning(f"Tentative {retries}/{max_retries} échouée - Erreur de connexion: {e}")
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

# --- WhatsApp Core Logic ---
class UniPileWhatsAppClient:
    def __init__(self, api_key: str, dsn: str):
        self.base_url = f"https://{dsn}/api/v1"
        self.headers = {"X-API-KEY": api_key, "Content-Type": "application/json", "Accept": "application/json"}

    @with_retry()
    def get_contact_id(self, phone: str) -> str:
        url = f"{self.base_url}/contacts"
        params = {"account_id": settings.whatsapp.account_id, "msisdn": phone}
        try:
            logger.debug(f"Recherche du contact Unipile pour {phone}")
            resp = requests.get(url, params=params, headers=self.headers, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                logger.warning(f"Aucun contact Unipile trouvé pour {phone}, utilisation du format standard @c.us")
                return f"{phone}@c.us"
            contact_id = data[0]["id"]
            logger.debug(f"ID de contact Unipile trouvé pour {phone}: {contact_id}")
            return contact_id
        except Exception as e:
            logger.error(f"Erreur lors de la recherche du contact Unipile pour {phone}: {e}. Utilisation de {phone}@c.us")
            return f"{phone}@c.us" # Fallback

    @with_retry()
    def send_message(self, phone: str, text: str) -> Dict[str, Any]:
        whatsapp_id = self.get_contact_id(phone)
        payload = {"account_id": settings.whatsapp.account_id, "text": text, "attendees_ids": [whatsapp_id]}
        url = f"{self.base_url}/chats"
        logger.debug(f"Envoi d'un message WhatsApp Unipile à {whatsapp_id}")
        resp = requests.post(url, json=payload, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    @with_retry()
    def send_message_to_existing_chat(self, chat_id: str, text: str) -> Dict[str, Any]:
        url = f"{self.base_url}/chats/{chat_id}/messages"
        payload = {"text": text}
        logger.debug(f"Envoi d'un message WhatsApp Unipile au chat {chat_id}")
        resp = requests.post(url, json=payload, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

def get_whatsapp_client() -> UniPileWhatsAppClient:
    api_key = settings.api_keys.unipile
    dsn = settings.whatsapp.unipile_dsn
    if not api_key or not dsn:
        logger.error("Clé API Unipile ou DSN manquant dans la configuration.")
        raise ValueError("Configuration Unipile incomplète.")
    return UniPileWhatsAppClient(api_key, dsn)

def format_phone_number(phone_number: str) -> str:
    if not phone_number: return ""
    cleaned = phone_number.strip()
    for char in [" ", "-", "(", ")", ".", "/", "\\", ":"]:
        cleaned = cleaned.replace(char, "")
    if ":" in cleaned: cleaned = cleaned.split(":")[-1].strip()
    if cleaned.startswith('+'): cleaned = cleaned[1:]
    digits = ''.join(ch for ch in cleaned if ch.isdigit())
    if digits.startswith('00'): digits = digits[2:]
    if not digits:
        logger.error(f"Numéro invalide (aucun chiffre): '{phone_number}'")
        return ""
    logger.debug(f"Numéro formaté: '{phone_number}' -> '{digits}'")
    return digits

# --- Email Core Logic ---
class EmailClient:
    def __init__(self, username: str, password: str, smtp_host: str, smtp_port: int, 
                 imap_host: str, imap_port: int, sender_name: Optional[str], use_tls: bool):
        self.username = username
        self.password = password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.sender_name = sender_name
        self.use_tls = use_tls
        logger.debug(f"Client Email initialisé pour {username} (SMTP: {smtp_host}:{smtp_port}, IMAP: {imap_host}:{imap_port})")

    def get_formatted_sender(self) -> str:
        return formataddr((self.sender_name, self.username)) if self.sender_name else self.username

    @with_retry(max_retries=2, delay=2) # Longer delay for email operations
    def send_email(self, to: List[str], subject: str, body: str, 
                   cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, 
                   attachments: Optional[List[str]] = None) -> Dict[str, Any]:
        if not to: return {"success": False, "error": "Aucun destinataire spécifié"}
        
        msg = MIMEMultipart()
        msg["From"] = self.get_formatted_sender()
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        if cc: msg["Cc"] = ", ".join(cc)
        
        body_type = "html" if any(tag in body.lower() for tag in ["<html", "<body", "<div", "<br"]) else "plain"
        msg.attach(MIMEText(body, body_type))

        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    logger.warning(f"Pièce jointe introuvable, ignorée: {file_path}")
                    continue
                try:
                    with open(file_path, "rb") as fp:
                        part = MIMEApplication(fp.read(), Name=os.path.basename(file_path))
                    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)
                    logger.debug(f"Pièce jointe ajoutée: {file_path}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de la pièce jointe {file_path}: {e}")
                    # Continue without this attachment

        all_recipients = list(to)
        if cc: all_recipients.extend(cc)
        if bcc: all_recipients.extend(bcc)

        try:
            logger.debug(f"Connexion SMTP à {self.smtp_host}:{self.smtp_port}")
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg, from_addr=self.username, to_addrs=all_recipients)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    if self.use_tls: server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg, from_addr=self.username, to_addrs=all_recipients)
            logger.info(f"Email envoyé à {len(all_recipients)} destinataires, sujet: {subject}")
            return {"success": True, "to": to, "cc": cc or [], "bcc": bcc or [], "subject": subject, "attachment_count": len(attachments) if attachments else 0}
        except smtplib.SMTPAuthenticationError as e:
            err_msg = f"Authentification SMTP échouée pour {self.username}: {e}"
            logger.error(err_msg)
            return {"success": False, "error": err_msg}
        except Exception as e:
            err_msg = f"Erreur SMTP lors de l'envoi: {e}"
            logger.error(err_msg, exc_info=True)
            return {"success": False, "error": err_msg}

    def _decode_header_value(self, header_value: Any) -> str:
        if not header_value: return ""
        decoded_parts = decode_header(str(header_value))
        return "".join(
            part.decode(encoding or 'utf-8', 'replace') if isinstance(part, bytes) else part
            for part, encoding in decoded_parts
        )

    def _parse_email_date(self, date_str: str) -> str:
        try:
            dt = email.utils.parsedate_to_datetime(date_str)
            return dt.astimezone(timezone.utc).isoformat() if dt else date_str
        except: return date_str

    def _get_email_body(self, msg_part: email.message.Message) -> str:
        content_type = msg_part.get_content_type()
        body_content = ""
        if msg_part.is_multipart():
            html_part = None
            plain_part = None
            for part in msg_part.walk():
                if part.get_content_type() == 'text/html':
                    html_part = part
                    break # Prefer HTML
                elif part.get_content_type() == 'text/plain':
                    plain_part = part
            target_part = html_part or plain_part
            if target_part:
                try:
                    payload = target_part.get_payload(decode=True)
                    charset = target_part.get_content_charset() or 'utf-8'
                    body_content = payload.decode(charset, 'replace')
                except Exception as e:
                    logger.warning(f"Erreur décodage partie email: {e}")
        else: # Not multipart
            if content_type in ['text/plain', 'text/html']:
                try:
                    payload = msg_part.get_payload(decode=True)
                    charset = msg_part.get_content_charset() or 'utf-8'
                    body_content = payload.decode(charset, 'replace')
                except Exception as e:
                    logger.warning(f"Erreur décodage corps email: {e}")
        return body_content

    @with_retry(max_retries=2, delay=2)
    def retrieve_emails(self, folder: str = "INBOX", limit: int = 10, 
                        unread_only: bool = False, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        emails_list = []
        try:
            logger.debug(f"Connexion IMAP à {self.imap_host}:{self.imap_port} pour {self.username}")
            with imaplib.IMAP4_SSL(self.imap_host, self.imap_port) as imap:
                imap.login(self.username, self.password)
                status, _ = imap.select(f'"{folder}"', readonly=True) # Use readonly for listing
                if status != 'OK':
                    logger.error(f"Dossier IMAP '{folder}' introuvable.")
                    return []

                search_criteria = []
                if unread_only: search_criteria.append('UNSEEN')
                if search_query: search_criteria.append(search_query)
                final_search_query = "ALL" if not search_criteria else f'({" ".join(search_criteria)})'
                
                logger.debug(f"Recherche IMAP avec critères: {final_search_query}")
                status, msg_ids_bytes = imap.search(None, final_search_query)
                if status != 'OK': 
                    logger.error(f"Erreur recherche IMAP: {final_search_query}")
                    return []

                msg_ids = [m_id for m_id in msg_ids_bytes[0].split() if m_id] # Filter empty IDs
                msg_ids.reverse() # Most recent first
                
                for msg_id in msg_ids[:limit]:
                    try:
                        status, msg_data = imap.fetch(msg_id, "(RFC822)")
                        if status != 'OK' or not msg_data[0] or not isinstance(msg_data[0], tuple):
                            logger.warning(f"Impossible de récupérer l'email ID {msg_id.decode()}")
                            continue
                        
                        raw_email = msg_data[0][1]
                        email_msg = email.message_from_bytes(raw_email)
                        
                        attachments_info = []
                        has_attachments = False
                        if email_msg.is_multipart():
                            for part in email_msg.walk():
                                cd = part.get("Content-Disposition")
                                if cd and "attachment" in cd.lower():
                                    filename = part.get_filename()
                                    if filename:
                                        attachments_info.append(self._decode_header_value(filename))
                                        has_attachments = True

                        email_data = {
                            "id": msg_id.decode(),
                            "from": self._decode_header_value(email_msg['From']),
                            "to": self._decode_header_value(email_msg['To']),
                            "cc": self._decode_header_value(email_msg['Cc']),
                            "subject": self._decode_header_value(email_msg['Subject']),
                            "date": self._parse_email_date(email_msg['Date']),
                            "body": self._get_email_body(email_msg),
                            "has_attachments": has_attachments,
                            "attachments": attachments_info
                        }
                        emails_list.append(email_data)
                    except Exception as e:
                        logger.error(f"Erreur traitement email ID {msg_id.decode()}: {e}", exc_info=False)
            logger.info(f"{len(emails_list)} emails récupérés de '{folder}' pour {self.username}")
            return emails_list
        except imaplib.IMAP4.error as e:
            logger.error(f"Erreur IMAP pour {self.username} sur {folder}: {e}")
            return [] # Return empty list on IMAP error
        except Exception as e:
            logger.error(f"Erreur inattendue récupération emails pour {self.username}: {e}", exc_info=True)
            return []

def get_email_client() -> EmailClient:
    cfg = settings.email
    if not all([cfg.username, cfg.password, cfg.smtp_host, cfg.smtp_port, cfg.imap_host, cfg.imap_port]):
        logger.error("Configuration email incomplète dans les paramètres.")
        raise ValueError("Configuration email (SMTP/IMAP) incomplète.")
    return EmailClient(username=cfg.username, password=cfg.password, 
                       smtp_host=cfg.smtp_host, smtp_port=cfg.smtp_port, 
                       imap_host=cfg.imap_host, imap_port=cfg.imap_port, 
                       sender_name=cfg.sender_name, use_tls=cfg.use_tls) 