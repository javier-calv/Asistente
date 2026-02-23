import logging
import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

from database import supabase
from services.notification_service import (
    obtener_recordatorios_pendientes,
    marcar_como_notificado,
    enviar_whatsapp,
    formatear_fecha,
    enviar_telegram
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def verificar_y_notificar():
    logger.info("🔍 Verificando recordatorios...")
    pendientes = obtener_recordatorios_pendientes(supabase)

    if not pendientes:
        logger.info("Sin recordatorios pendientes.")
        return

    for r in pendientes:
        try:
            usuarios = r.get("Usuarios")
            if not usuarios:
                logger.warning(f"Recordatorio {r['id']} sin usuario, saltando.")
                continue

            identificador = usuarios.get("user_phone")
            if not identificador:
                logger.warning(f"Recordatorio {r['id']} sin identificador, saltando.")
                continue

            tarea   = r["task_description"]
            hora    = formatear_fecha(r["execution_time"])
            mensaje = (
                f"🔔 *Recordatorio*\n"
                f"📌 {tarea}\n"
                f"🕐 {hora}"
            )

            # Detectar canal por prefijo
            if identificador.startswith("telegram_"):
                chat_id = identificador.replace("telegram_", "")
                enviado = enviar_telegram(chat_id, mensaje)
            else:
                enviado = enviar_whatsapp(identificador, mensaje)

            if enviado:
                marcar_como_notificado(supabase, r["id"])
                logger.info(f"✅ Recordatorio {r['id']} notificado.")
            else:
                logger.warning(f"⚠️ No se pudo notificar recordatorio {r['id']}.")

        except Exception as e:
            logger.error(f"Error procesando recordatorio {r.get('id')}: {e}", exc_info=True)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(verificar_y_notificar, "interval", minutes=1)

    logger.info("🚀 Scheduler iniciado. Verificando cada minuto...")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("⛔ Scheduler detenido.")