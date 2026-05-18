import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Nuevo Jugador")

name = st.text_input("Nombre")
email = st.text_input("Email")

if st.button("Crear jugador"):

    try:

        response = supabase.table("players").insert({
            "name": name,
            "email": email
        }).execute()

        st.success("Jugador creado")
        st.write(response.data)

    except Exception as e:
        st.error(str(e))