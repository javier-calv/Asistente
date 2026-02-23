from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import logging

from database import supabase
from ia import procesar_mensaje_completo
from services.user_service import obtener_o_crear_usuario
from services.reminder_service import guardar_recordatorio, eliminar_recordatorio, consultar_recordatorios

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route("/webhook", methods=['POST'])
def webhook():
    mensaje_entrada = request.values.get('Body', '').strip()
    numero_usuario  = request.values.get('From', '').replace('whatsapp:', '').strip()

    if not mensaje_entrada or not numero_usuario:
        return "Bad Request", 400

    u_id = obtener_o_crear_usuario(supabase, numero_usuario)
    resultado = procesar_mensaje_completo(mensaje_entrada)

    instrucciones = resultado["instrucciones"]
    respuesta_final = resultado["respuesta"]

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
                lista = [t['task_description'] for t in query.data] if query.data else []
                if lista:
                    respuesta_final = f"Para el {fecha_dia} tienes: {', '.join(lista)} 📋"
                else:
                    respuesta_final = f"No tienes nada agendado para el {fecha_dia}. 🗓️"

        except Exception as e:
            logger.error(f"Error en {accion} ('{tarea}'): {e}", exc_info=True)
            respuesta_final = "Hubo un problema al procesar. Intenta de nuevo. 🙏"

    resp = MessagingResponse()
    resp.message(respuesta_final)
    return str(resp)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(port=5000, debug=True)