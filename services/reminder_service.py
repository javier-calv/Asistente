# services/reminder_service.py

def guardar_recordatorio(supabase, u_id, tarea, fecha_hora):
    return supabase.table("Recordatorios").insert({
        "user_id": u_id,
        "task_description": tarea,
        "execution_time": fecha_hora,
        "status": "pendiente"
    }).execute()

def eliminar_recordatorio(supabase, u_id, tarea):
    return supabase.table("Recordatorios").delete() \
        .eq("user_id", u_id) \
        .ilike("task_description", f"%{tarea}%") \
        .execute()

def consultar_recordatorios(supabase, u_id, fecha_dia):
    inicio = f"{fecha_dia} 00:00:00"
    fin = f"{fecha_dia} 23:59:59"
    return supabase.table("Recordatorios").select("*") \
        .eq("user_id", u_id) \
        .gte("execution_time", inicio) \
        .lte("execution_time", fin) \
        .execute()