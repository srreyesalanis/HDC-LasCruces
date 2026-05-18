import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Golf Handicap")

course = st.selectbox("Campo", ["Las Cruces"])

score = st.number_input("Score Hoyo 1", min_value=1, max_value=15)

if st.button("Guardar Round"):
    supabase.table("round_holes").insert({
        "hole_number": 1,
        "strokes": score
    }).execute()

    st.success("Guardado")