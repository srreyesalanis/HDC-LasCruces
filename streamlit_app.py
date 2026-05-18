import streamlit as st
from supabase import create_client
from datetime import datetime

# Conexion
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

st.title("Nuevo Round")

# DATOS DE EJEMPLO
player_id = "UUID_DEL_PLAYER"
course_id = "UUID_DEL_CURSO"

hole_number = st.number_input(
    "Hoyo",
    min_value=1,
    max_value=18,
    step=1
)

strokes = st.number_input(
    "Golpes",
    min_value=1,
    max_value=15,
    step=1
)

if st.button("Guardar Round"):

    try:

        # 1. Crear round
        round_response = supabase.table("rounds").insert({
            "player_id": player_id,
            "course_id": course_id,
            "played_at": datetime.now().isoformat()
        }).execute()

        # 2. Obtener round_id
        round_id = round_response.data[0]["id"]

        # 3. Guardar hoyo
        hole_response = supabase.table("round_holes").insert({
            "round_id": round_id,
            "hole_number": hole_number,
            "strokes": strokes
        }).execute()

        st.success("Round guardado")

        st.write(hole_response.data)

    except Exception as e:
        st.error(str(e))