import os
from dotenv  import load_dotenv
from supabase import create_client, Client

load_dotenv ()

url : str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client =create_client(url, key)

def probar_conexion():
    try:
        data={
            "user_phone": "573000000000",
            "task_description" : "prubea para ver si soy la monda",
            "status" : "pendiente"
        }
        response= supabase.table ("Recordatorios").insert(data).execute()
        print ("conexcion mas que mela")
        return response
    
    except Exception as e: 
        print (f"eror al conectar {e}")
        return None
    
if __name__ =="__main__":
        probar_conexion()