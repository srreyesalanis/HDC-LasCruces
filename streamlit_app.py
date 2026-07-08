mport streamlit as st
import pandas as pd
import uuid
from datetime import date, datetime as _dt_global
from zoneinfo import ZoneInfo
_TZ_CST = ZoneInfo("America/Monterrey")
from total_adjusted_app import calcular_total_ajustado
from differential_app import calcular_differential
from handicap_index import calcular_handicap_index

from supabase import create_client

# Conexion
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

@st.cache_data(ttl=30)
def get_courses():
    try:
        return supabase.table("courses").select("*").execute().data or []
    except Exception:
        return []

@st.cache_data(ttl=30)
def get_players():
    try:
        return supabase.table("players").select("*").order("name").execute().data or []
    except Exception:
        return []

@st.cache_data(ttl=30)
def get_tees(course_id):
    try:
        return supabase.table("tees").select("*").eq("course_id", course_id).execute().data or []
    except Exception:
        return []

@st.cache_data(ttl=60)
def get_rounds(player_id):
    try:
        return supabase.table("rounds").select("*").eq("player_id", player_id).order("played_at", desc=True).execute().data or []
    except Exception:
        return []

@st.cache_data(ttl=60)
def get_torneos():
    try:
        return supabase.table("tournaments").select("id, name, date, format").order("date", desc=True).execute().data or []
    except Exception:
        return []

@st.cache_data(ttl=60)
def get_grupos(torneo_id):
    try:
        return supabase.table("groups").select("id, name").eq("tournament_id", torneo_id).execute().data or []
    except Exception:
        return []

@st.cache_data(ttl=60)
def get_group_players(group_id):
    try:
        return supabase.table("group_players").select("id, player_id, guest_id, player_name").eq("group_id", group_id).execute().data or []
    except Exception:
        return []

@st.cache_data(ttl=60)
def get_tournament_scores(torneo_id):
    try:
        return supabase.table("tournament_scores").select("player_id, guest_id, hole_number, strokes").eq("tournament_id", torneo_id).execute().data or []
    except Exception:
        return []

st.title("Golf Handicap - Las Cruces")

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
            import io, sys, traceback
            _old_stdout = sys.stdout
            _old_stderr = sys.stderr
            sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')
            sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
            finally:
                sys.stdout = _old_stdout
                sys.stderr = _old_stderr

            if response and response.user:
                st.session_state.user = response.user
                st.success("Login correcto")
                st.rerun()
            else:
                st.error("Login fallido: respuesta invalida.")

        except Exception as e:
            _tb = traceback.format_exc()
            _tb_safe = _tb.encode('ascii', 'replace').decode('ascii')
            st.error("Traceback: " + _tb_safe[-500:])

# APP
else:

    # LOGOUT ARRIBA DERECHA
    top_col1, top_col2 = st.columns([8, 1])

    with top_col2:

        logout_button = st.button(
        "Cerrar Sesion",
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

    tab_jugador, tab_ronda, tab_mod = st.tabs(["Crear Jugador", "Crear Ronda", "Modificar Ronda"])

    # PAGINA CREAR JUGADOR
    with tab_jugador:

        st.header("Nuevo Jugador")

        name = st.text_input("Nombre")
        email = st.text_input("Email")

        if st.button("Guardar Jugador"):
            try:
                supabase.table("players").insert({"name": name, "email": email}).execute()
                st.success("Jugador creado")
            except Exception:
                st.error("Error al guardar jugador.")


    # PAGINA CREAR RONDA
    with tab_ronda:

        st.header("Nueva Ronda")

        courses = supabase.table("courses").select("*").execute().data
        course_options = {c["name"]: c["id"] for c in courses}

        selected_course_name = st.selectbox("Selecciona el Campo", list(course_options.keys()), index=None, placeholder="Selecciona un campo...")

        if selected_course_name:
            selected_course_id = course_options[selected_course_name]

            tees = supabase.table("tees").select("*").eq("course_id", selected_course_id).execute().data
            tee_options = {t["color"]: t["id"] for t in tees}

            selected_tee_name = st.selectbox("Selecciona las Tees", list(tee_options.keys()), index=None, placeholder="Selecciona las tees...")

            if selected_tee_name:
                selected_tee_id = tee_options[selected_tee_name]
                selected_tee = next(t for t in tees if t["id"] == selected_tee_id)
                slope_rating = selected_tee["slope"]
                course_rating = selected_tee["rating"]

                round_date = st.date_input("Fecha de la ronda", value=_dt_global.now(_TZ_CST).date())

                players_response = supabase.table("players").select("*").order("name").execute().data
                player_options = {p["name"]: p["id"] for p in players_response}

                selected_player_name = st.selectbox("Jugador", list(player_options.keys()), index=None, placeholder="Selecciona un jugador...")

                if selected_player_name:
                    player_id = player_options[selected_player_name]

                    front_df = pd.DataFrame({"Hoyo": list(range(1,10)),  "Score": [0]*9})
                    back_df  = pd.DataFrame({"Hoyo": list(range(10,19)), "Score": [0]*9})

                    st.subheader("Front 9")
                    front_scores = st.data_editor(front_df, hide_index=True, use_container_width=True)
                    st.subheader("Back 9")
                    back_scores  = st.data_editor(back_df,  hide_index=True, use_container_width=True)

                    front_total = front_scores["Score"].sum()
                    back_total  = back_scores["Score"].sum()
                    total = front_total + back_total

                    st.markdown("---")
                    st.write(f"Front: {front_total} | Back: {back_total} | Total: {total}")

                    if st.button("Guardar Ronda"):
                        round_id = str(uuid.uuid4())
                        supabase.table("rounds").insert({
                            "round_id": round_id, "player_id": player_id,
                            "course_id": selected_course_id, "tee_id": selected_tee_id,
                            "played_at": str(round_date), "total_score": int(total),
                        }).execute()
                        for _, row in pd.concat([front_scores, back_scores]).iterrows():
                            supabase.table("round_holes").insert({
                                "round_id": round_id, "hole_number": int(row["Hoyo"]), "strokes": int(row["Score"])
                            }).execute()
                        adjusted_total = calcular_total_ajustado(supabase, selected_course_id, round_id)
                        differential   = calcular_differential(supabase, adjusted_total, course_rating, round_id, slope_rating)
                        handicap_index = calcular_handicap_index(supabase, player_id)
                        st.success("Ronda guardada")





    # PAGINA MODIFICAR RONDA
    with tab_mod:

        st.header("Modificar Ronda")

        players_mod = supabase.table("players").select("*").order("name").execute().data
        player_options_mod = {p["name"]: p["id"] for p in players_mod}

        selected_player_mod = st.selectbox("Jugador", list(player_options_mod.keys()), index=None, placeholder="Selecciona un jugador...", key="mod_player")
        if selected_player_mod:
            player_id_mod = player_options_mod[selected_player_mod]

            rounds_data = supabase.table("rounds") \
                .select("*") \
                .eq("player_id", player_id_mod) \
                .order("played_at", desc=True) \
                .execute().data

            if not rounds_data:
                st.info("Este jugador no tiene rondas registradas.")
            else:
                def round_label(r):
                    diff = r.get("differential", "N/A")
                    return f"{r['played_at']} - Total: {r['total_score']} | Diferencial: {diff}"

                round_options = {round_label(r): r["round_id"] for r in rounds_data}

                selected_round_label = st.selectbox("Ronda a modificar", list(round_options.keys()), key="mod_round")
                selected_round_id = round_options[selected_round_label]
                selected_round = next(r for r in rounds_data if r["round_id"] == selected_round_id)

                all_courses = supabase.table("courses").select("*").execute().data
                course_options_mod = {c["name"]: c["id"] for c in all_courses}
                current_course = next((c["name"] for c in all_courses if c["id"] == selected_round["course_id"]), list(course_options_mod.keys())[0])
                selected_course_mod = st.selectbox("Campo", list(course_options_mod.keys()), index=list(course_options_mod.keys()).index(current_course), key="mod_course")
                selected_course_id_mod = course_options_mod[selected_course_mod]

                all_tees = supabase.table("tees").select("*").eq("course_id", selected_course_id_mod).execute().data
                tee_options_mod = {t["color"]: t["id"] for t in all_tees}
                current_tee = next((t["color"] for t in all_tees if t["id"] == selected_round["tee_id"]), list(tee_options_mod.keys())[0])
                tee_default_idx = list(tee_options_mod.keys()).index(current_tee) if current_tee in tee_options_mod else 0
                selected_tee_mod = st.selectbox("Tees", list(tee_options_mod.keys()), index=tee_default_idx, key="mod_tee")
                selected_tee_id_mod = tee_options_mod[selected_tee_mod]
                tee_mod = next(t for t in all_tees if t["id"] == selected_tee_id_mod)

                from datetime import date as _date, datetime as _datetime
                current_date = _datetime.strptime(selected_round["played_at"], "%Y-%m-%d").date() if selected_round.get("played_at") else _dt_global.now(_TZ_CST).date()
                new_date = st.date_input("Fecha de la ronda", value=current_date, key="mod_date")

                holes_data = {h["hole_number"]: h["strokes"] for h in supabase.table("round_holes").select("*").eq("round_id", selected_round_id).execute().data}
                front_df_mod = pd.DataFrame({"Hoyo": list(range(1, 10)),  "Score": [holes_data.get(h, 0) for h in range(1, 10)]})
                back_df_mod  = pd.DataFrame({"Hoyo": list(range(10, 19)), "Score": [holes_data.get(h, 0) for h in range(10, 19)]})

                st.subheader("Front 9")
                front_mod = st.data_editor(front_df_mod, hide_index=True, use_container_width=True, key="mod_front")
                st.subheader("Back 9")
                back_mod  = st.data_editor(back_df_mod,  hide_index=True, use_container_width=True, key="mod_back")

                front_total_mod = front_mod["Score"].sum()
                back_total_mod  = back_mod["Score"].sum()
                total_mod       = front_total_mod + back_total_mod

                st.markdown("---")
                st.write(f"Front: {front_total_mod} | Back: {back_total_mod} | Total: {total_mod}")

                col_save, col_del = st.columns(2)
                with col_save:
                    if st.button("Guardar cambios", use_container_width=True):
                        supabase.table("rounds").update({
                            "total_score": int(total_mod), "tee_id": selected_tee_id_mod,
                            "course_id": selected_course_id_mod, "played_at": str(new_date)
                        }).eq("round_id", selected_round_id).execute()
                        for _, row in pd.concat([front_mod, back_mod]).iterrows():
                            supabase.table("round_holes").update({"strokes": int(row["Score"])}).eq("round_id", selected_round_id).eq("hole_number", int(row["Hoyo"])).execute()
                        adjusted_total_mod = calcular_total_ajustado(supabase, selected_course_id_mod, selected_round_id)
                        differential_mod   = calcular_differential(supabase, adjusted_total_mod, tee_mod["rating"], selected_round_id, tee_mod["slope"])
                        handicap_mod       = calcular_handicap_index(supabase, player_id_mod)
                        hdc_str = str(handicap_mod) if handicap_mod is not None else "Sin datos suficientes"
                        st.success(f"Ronda actualizada. Diferencial: {differential_mod} | Handicap Index: {hdc_str}")
                with col_del:
                    if st.button("Borrar ronda", use_container_width=True, type="primary"):
                        st.session_state["confirm_delete"] = selected_round_id

                if st.session_state.get("confirm_delete") == selected_round_id:
                    st.warning("Seguro que quieres borrar esta ronda? Esta accion no se puede deshacer.")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Si, borrar", use_container_width=True):
                            supabase.table("round_holes").delete().eq("round_id", selected_round_id).execute()
                            supabase.table("rounds").delete().eq("round_id", selected_round_id).execute()
                            calcular_handicap_index(supabase, player_id_mod)
                            st.session_state["confirm_delete"] = None
                            st.success("Ronda eliminada y handicap recalculado.")
                            st.rerun()
                    with col_no:
                        if st.button("Cancelar", use_container_width=True):
                            st.session_state["confirm_delete"] = None
                            st.rerun()
