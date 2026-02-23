import datetime
import re
import logging

logger = logging.getLogger(__name__)

_PATRONES_CONSULTA = [
    (r"\b(hoy)\b",               0),
    (r"\b(mañana)\b",            1),
    (r"\b(pasado\s*mañana)\b",   2),
    (r"\ben\s+(\d+)\s+d[ií]as?\b", "n_dias"),
]

_PALABRAS_CONSULTA = [
    "qué tengo", "que tengo", "tengo algo", "pendiente",
    "pendientes", "agenda", "agendado", "recordatorio",
    "recordatorios", "hay algo", "tienes algo"
]

def detectar_consulta_rapida(texto: str) -> dict | None:
    """
    Si el mensaje es claramente una consulta simple,
    retorna el dict sin llamar a Gemini. Si no, retorna None.
    """
    texto_lower = texto.lower()

    es_consulta = any(p in texto_lower for p in _PALABRAS_CONSULTA)
    if not es_consulta:
        return None

    ahora = datetime.datetime.now()
    fecha_objetivo = None

    for patron, delta in _PATRONES_CONSULTA:
        match = re.search(patron, texto_lower)
        if match:
            if delta == "n_dias":
                n = int(match.group(1))
                fecha_objetivo = (ahora + datetime.timedelta(days=n)).date()
            else:
                fecha_objetivo = (ahora + datetime.timedelta(days=delta)).date()
            break

    if not fecha_objetivo:
        return None  # Sin referencia temporal clara → que lo maneje Gemini

    fecha_str = fecha_objetivo.strftime("%Y-%m-%d")
    logger.info(f"[FAST] Consulta rápida detectada para {fecha_str}")

    return {
        "instrucciones": [f"CONSULTAR|N/A|{fecha_str} 00:00:00"],
        "respuesta": None  # app.py lo reemplaza con datos reales de DB
    }