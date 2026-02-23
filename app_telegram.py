from flask import Flask, request
import logging
import requests
import os
from dotenv import load_dotenv

from database import supabase
from ia import procesar_mensaje_completo
from services.user_service import obtener_o_crear_usuario
from services.reminder_service import guardar_recordatorio, eliminar_recordatorio, consultar_recordatorios

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def enviar_mensaje_telegram(chat_id: int, texto: str) -> None:
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id":    chat_id,
            "text":       texto,
            "parse_mode": "Markdown"
        })
    except Exception as e:
        logger.error(f"Error enviando mensaje Telegram: {e}", exc_info=True)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return "Bad Request", 400

    message = data.get("message")
    if not message or "text" not in message:
        return "OK", 200

    chat_id         = message["chat"]["id"]
    mensaje_entrada = message["text"].strip()
    # Prefijo telegram_ para distinguirlo de WhatsApp en Supabase
    numero_usuario  = f"telegram_{message['from']['id']}"

    if not mensaje_entrada:
        return "OK", 200

    # 1. Identificar usuario
    u_id = obtener_o_crear_usuario(supabase, numero_usuario)
    if not u_id:
        enviar_mensaje_telegram(chat_id, "Hubo un problema identificándote. Intenta de nuevo. 🙏")
        return "OK", 200

    # 2. Una sola llamada a Gemini (o fast reply)
    resultado       = procesar_mensaje_completo(mensaje_entrada)
    instrucciones   = resultado["instrucciones"]
    respuesta_final = resultado["respuesta"]

    # 3. Ejecutar instrucciones en DB
    for item in instrucciones:
        partes = [p.strip() for p in item.split("|", 2)]
        if len(partes) < 3:
            continue

        accion, tarea, fecha_hora = partes[0].upper(), partes[1], partes[2]

        if not tarea or not fecha_hora:
            continue

        try:
            if accion == "GUARDAR":
                guardar_recordatorio(supabase, u_id, tarea, fecha_hora)

            elif accion == "ELIMINAR":
                eliminar_recordatorio(supabase, u_id, tarea)

            elif accion == "CONSULTAR":
                fecha_dia = fecha_hora.split()[0]
                query = consultar_recordatorios(supabase, u_id, fecha_dia)
                lista = [t["task_description"] for t in query.data] if query.data else []
                if lista:
                    items = "\n".join(f"• {t}" for t in lista)
                    respuesta_final = f"📋 *Tienes para el {fecha_dia}:*\n{items}"
                else:
                    respuesta_final = f"No tienes nada agendado para el {fecha_dia}. 🗓️"

        except Exception as e:
            logger.error(f"Error en {accion} ('{tarea}'): {e}", exc_info=True)
            respuesta_final = "Hubo un problema al procesar. Intenta de nuevo. 🙏"

    # 4. Responder al usuario
    enviar_mensaje_telegram(chat_id, respuesta_final)
    return "OK", 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)