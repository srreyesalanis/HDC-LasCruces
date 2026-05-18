
import streamlit as st
import pandas as pd

from supabase import create_client

# Conexion
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

st.title("⛳ Golf Handicap - Las Cruces")

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
    st.markdown("""
        <style>

       .red-button button {
        background-color: #d32f2f !important;
        color: white !important;
        }

        .red-button button:hover {
            background-color: #b71c1c !important;
            color: white !important;
        }

        .green-button button {
            background-color: #2e7d32 !important;
            color: white !important;
        }

        .green-button button:hover {
            background-color: #1b5e20 !important;
            color: white !important;
        }

        </style>
        """, unsafe_allow_html=True)

    # LOGOUT ARRIBA DERECHA
    top_col1, top_col2 = st.columns([8, 1])

    with top_col2:

        logout_button = st.button(
        "Cerrar sesión",
        type="primary",
        use_container_width=True,
        key="logout_button"
        )

        if logout_button:

            supabase.auth.sign_out()

            st.session_state.user = None

            st.rerun()

    st.success(
        f"Bienvenido {st.session_state.user.email}"
        
    )
    st.markdown("---")

    st.subheader("Menú Principal")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👤 Crear Jugador", type="secondary", use_container_width=True):
            st.session_state["page"] = "crear_jugador"

    with col2:
        if st.button("🏌️ Crear Ronda", type="secondary", use_container_width=True):
            st.session_state["page"] = "crear_ronda"

    st.markdown("---")

    # PAGINA CREAR JUGADOR
    if st.session_state.get("page") == "crear_jugador":

        st.header("👤 Nuevo Jugador")

        name = st.text_input("Nombre")
        email = st.text_input("Email")

        if st.button("Guardar Jugador"):

            from supabase import create_client

            SUPABASE_URL = st.secrets["SUPABASE_URL"]
            SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


            try:

                    response = supabase.table("players").insert({
                        "name": name,
                        "email": email
                    }).execute()

                    st.success("Jugador creado")
                    st.write(response.data)

            except Exception as e:
                    st.error(str(e))

    # PAGINA CREAR RONDA
    if st.session_state.get("page") == "crear_ronda":

        st.header("🏌️ Nueva Ronda")

        from supabase import create_client

        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Obtener jugadores desde Supabase
        players_response = supabase.table("players").select("*").order("name").execute()

        players = players_response.data

        # Crear diccionario nombre -> id
        player_options = {
        player["name"]: player["id"]
        for player in players
        }

        # Selectbox
        selected_player_name = st.selectbox(
        "Jugador",
            list(player_options.keys())
    )

        # Obtener UUID del jugador seleccionado
        player_id = player_options[selected_player_name]

        # FRONT 9
        front_df = pd.DataFrame({
            "Hoyo": [1,2,3,4,5,6,7,8,9],
            "Score": [0,0,0,0,0,0,0,0,0]
        })

        # BACK 9
        back_df = pd.DataFrame({
            "Hoyo": [10,11,12,13,14,15,16,17,18],
            "Score": [0,0,0,0,0,0,0,0,0]
        })

        st.subheader("Front 9")

        front_scores = st.data_editor(
            front_df,
            hide_index=True,
            use_container_width=True
        )

        st.subheader("Back 9")

        back_scores = st.data_editor(
            back_df,
            hide_index=True,
            use_container_width=True
        )

        # Totales
        front_total = front_scores["Score"].sum()
        back_total = back_scores["Score"].sum()

        total = front_total + back_total

        st.markdown("---")

        st.write(f"Front: {front_total}")
        st.write(f"Back: {back_total}")
        st.write(f"Total: {total}")
        if st.button("Guardar Ronda"):

            for _, row in front_scores.iterrows():

                supabase.table("round_holes").insert({
                    "round_id": round_id,
                    "hole_number": int(row["Hoyo"]),
                    "strokes": int(row["Score"])
                }).execute()

            for _, row in back_scores.iterrows():

                supabase.table("round_holes").insert({
                    "round_id": round_id,
                    "hole_number": int(row["Hoyo"]),
                    "strokes": int(row["Score"])
                }).execute()

            st.success("Ronda guardada")




