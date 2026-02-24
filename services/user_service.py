import logging

logger = logging.getLogger(__name__)

# Zonas horarias por código de país de Telegram
_ZONAS_HORARIAS = {
    "es": "Europe/Madrid",
    "mx": "America/Mexico_City",
    "ar": "America/Argentina/Buenos_Aires",
    "co": "America/Bogota",
    "pe": "America/Lima",
    "cl": "America/Santiago",
    "ve": "America/Caracas",
    "us": "America/New_York",
}

def obtener_o_crear_usuario(supabase, numero_whatsapp: str, language_code: str = None):
    """
    Busca un usuario por teléfono. Si no existe, lo crea.
    Retorna el ID numérico o lanza excepción si falla.
    """
    if not numero_whatsapp or not numero_whatsapp.strip():
        raise ValueError("Número vacío o inválido.")

    numero = numero_whatsapp.strip()

    res = supabase.table("Usuarios") \
        .select("id, timezone") \
        .eq("user_phone", numero) \
        .limit(1) \
        .execute()

    if res.data:
        return res.data[0]["id"], res.data[0].get("timezone", "America/Bogota")

    # Detectar zona horaria por idioma
    timezone = _ZONAS_HORARIAS.get(language_code, "America/Bogota")

    logger.info(f"Registrando nuevo usuario: {numero} | timezone: {timezone}")
    nuevo = supabase.table("Usuarios").insert({
        "user_phone": numero,
        "name":       "Nuevo Usuario",
        "timezone":   timezone
    }).execute()

    if nuevo.data:
        return nuevo.data[0]["id"], timezone

    raise RuntimeError(f"No se pudo crear el usuario para {numero}.")