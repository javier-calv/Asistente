import os
import logging
import datetime
from datetime import timezone, timedelta
from google import genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
from services.fast_reply_service import detectar_consulta_rapida

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

_SYSTEM_PROMPT = """\
Eres un asistente de recordatorios. Responde SIEMPRE en este formato exacto:

VERBO|tarea|YYYY-MM-DD HH:MM:SS
RESPUESTA: texto corto y amigable con emojis

VERBO debe ser exactamente una de estas palabras: GUARDAR, CONSULTAR, ELIMINAR
Ejemplos:
GUARDAR|reunion con el jefe|2026-02-23 09:00:00
RESPUESTA: ¡Listo, reunión agendada! 📅

CONSULTAR|N/A|2026-02-23 00:00:00
RESPUESTA: Déjame revisar tu día 👀

ELIMINAR|reunion con el jefe|2026-02-23 00:00:00
RESPUESTA: ¡Eliminado! 🗑️

REGLAS:
- Si es CONSULTAR, tarea siempre es N/A
- Si pide cambiar algo: escribe ELIMINAR y luego GUARDAR en líneas separadas, antes de RESPUESTA
- La fecha y hora SIEMPRE deben estar completas en formato YYYY-MM-DD HH:MM:SS
- Sin markdown, sin explicaciones, nada más

REGLAS DE HORA (cuando el usuario no especifica hora exacta):
- Sin hora mencionada → 09:00:00
- "en la mañana" → 08:00:00
- "al medio día" o "a mediodía" → 12:00:00
- "en la tarde" → 15:00:00
- "en la noche" → 19:00:00\
"""
def procesar_mensaje_completo(texto_usuario: str) -> dict:
    rapido = detectar_consulta_rapida(texto_usuario)
    if rapido:
        return rapido

    ahora = datetime.datetime.now()  # hora local Colombia

    prompt = (
        f"{_SYSTEM_PROMPT}\n\n"
        f"Fecha actual: {ahora:%Y-%m-%d} | Hora actual: {ahora:%H:%M:%S}\n"
        f"Mensaje del usuario: {texto_usuario}"
    )
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={"max_output_tokens": 500}
        )
        texto_crudo = response.text.strip()
        logger.info(f"Gemini raw: {repr(texto_crudo)}")
        return _parsear_respuesta(texto_crudo)

    except google_exceptions.ResourceExhausted:
        logger.error("Cuota de Gemini agotada.")
        return {"instrucciones": [], "respuesta": "Estoy al límite, intenta en unos minutos. ⏳"}

    except Exception as e:
        logger.error(f"Error Gemini: {e}", exc_info=True)
        return {"instrucciones": [], "respuesta": "No pude procesar tu mensaje. Intenta de nuevo. 🙏"}


def _parsear_respuesta(texto: str) -> dict:
    instrucciones = []
    respuesta = None

    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if linea.upper().startswith("RESPUESTA:"):
            respuesta = linea[len("RESPUESTA:"):].strip()
        elif "|" in linea:
            if len(linea.split("|")) == 3:
                instrucciones.append(linea)
            else:
                logger.warning(f"Línea incompleta ignorada: {repr(linea)}")

    if not respuesta:
        respuesta = "¡Listo! Ya lo tengo anotado. 😊" if instrucciones else \
                    "No entendí qué anotar. ¿Me das más detalles? 😊"

    return {"instrucciones": instrucciones, "respuesta": respuesta}