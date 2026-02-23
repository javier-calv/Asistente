
def obtener_o_crear_usuario(supabase, numero_whatsapp):
    """
    Busca un usuario por su teléfono en la columna 'user_phone'. 
    Si no existe, lo crea.
    """
    res = supabase.table("Usuarios").select("id").eq("user_phone", numero_whatsapp).execute()

    if res.data:
        return res.data[0]['id']
    
    print(f"Registrando nuevo usuario: {numero_whatsapp}")
    nuevo = supabase.table("Usuarios").insert({
        "user_phone": numero_whatsapp,
        "name": "Nuevo Usuario"
    }).execute()
    
    if nuevo.data:
        return nuevo.data[0]['id']
    
    return None