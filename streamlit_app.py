
import streamlit as st
import pandas as pd

from supabase import create_client

# Conexion
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

st.title("⛳ Golf Handicap")

# Session state
if "user" not in st.session_state:
    st.session_state.user = None

# LOGIN
if st.session_state.user is None:

    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Entrar"):

        try:

            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            st.session_state.user = response.user

            st.success("Login correcto")

            st.rerun()

        except Exception as e:
            st.error(str(e))

# APP
else:


    st.success(
        f"Bienvenido {st.session_state.user.email}"
        
    )
    st.set_page_config(
    page_title="Golf Handicap",
    page_icon="⛳",
    layout="centered"
    
)