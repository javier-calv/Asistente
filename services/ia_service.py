# services/ia_service.py
from ia import model # Importas tu modelo configurado

def humanizar_respuesta(acciones_realizadas, mensaje_original):
    """
    Toma lo que el bot hizo y lo redacta de forma natural.
    """
    prompt = f"""
    Eres un asistente personal amable y eficiente. 
    El usuario dijo: "{mensaje_original}"
    
    Tú ya ejecutaste estas acciones en la base de datos:
    {acciones_realizadas}
    
    Redacta una respuesta confirmando lo que hiciste de forma natural, 
    cercana y breve (máximo 2 frases). Usa emojis si es oportuno.
    No digas "He ejecutado las acciones", di algo como "¡Listo! Ya te anoté el partido..."
    """
    
    respuesta = model.generate_content(prompt)
    return respuesta.text