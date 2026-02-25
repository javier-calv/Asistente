import logging
import os
from datetime import datetime, timezone, timedelta
from twilio.rest import Client
import requests

logger = logging.getLogger(__name__)

def formatear_fecha(fecha_str: str) -> str:
    try:
        fecha = datetime.fromisoformat(fecha_str)
        # Forzar conversión directa a UTC-5 sin depender del TZ del servidor
        utc_offset = fecha.utcoffset()
        if utc_offset is not None:
            fecha_utc = fecha.replace(tzinfo=timezone.utc) - utc_offset
            fecha = fecha_utc - timedelta(hours=0)  # ya está en UTC
            fecha = fecha.replace(tzinfo=None) 
            # Restar 5 horas para Colombia
            fecha = fecha - timedelta(hours=5)
        return fecha.strftime("%d/%m/%Y a las %I:%M %p")
    except Exception:
        return fecha_str
def enviar_whatsapp(numero_destino: str, mensaje: str) -> bool:
    """
    Envía un mensaje de WhatsApp via Twilio al usuario.
    """
    try:
        client = Client(
            os.environ.get("TWILIO_ACCOUNT_SID"),
            os.environ.get("TWILIO_AUTH_TOKEN")
        )
        client.messages.create(
            from_=f"whatsapp:{os.environ.get('TWILIO_WHATSAPP_NUMBER')}",
            to=f"whatsapp:{numero_destino}",
            body=mensaje
        )
        logger.info(f"✅ Notificación enviada a {numero_destino}")
        return True

    except Exception as e:
        logger.error(f"Error enviando WhatsApp a {numero_destino}: {e}", exc_info=True)
        return False

def enviar_telegram(chat_id: str, mensaje: str) -> bool:
    """
    Envía un mensaje por Telegram.
    """
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        res = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id":    chat_id,
                "text":       mensaje,
                "parse_mode": "Markdown"
            }
        )
        if res.status_code == 200:
            logger.info(f"✅ Telegram enviado a {chat_id}")
            return True
        logger.error(f"Telegram respondió {res.status_code}: {res.text}")
        return False
    except Exception as e:
        logger.error(f"Error enviando Telegram a {chat_id}: {e}", exc_info=True)
        return False

def obtener_recordatorios_pendientes(supabase) -> list:
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # hora local Colombia

    res = supabase.table("Recordatorios") \
        .select("id, task_description, execution_time, user_id, Usuarios(user_phone)") \
        .eq("status", "pendiente") \
        .lte("execution_time", ahora) \
        .execute()

    return res.data if res.data else []

def marcar_como_notificado(supabase, recordatorio_id: int) -> None:
    """
    Cambia el status a 'notificado' para no volver a enviar.
    """
    supabase.table("Recordatorios") \
        .update({"status": "notificado"}) \
        .eq("id", recordatorio_id) \
        .execute()
    
    