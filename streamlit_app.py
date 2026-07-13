import streamlit as st
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

st.title("â›³ Golf Handicap - Las Cruces")

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

    # LOGOUT ARRIBA DERECHA
    top_col1, top_col2 = st.columns([8, 1])

    with top_col2:

        logout_button = st.button(
        "Cerrar SesiÃ³n",
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

    st.subheader("MenÃº Principal")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("ðŸ‘¤ Crear Jugador", use_container_width=True):
            st.session_state["page"] = "crear_jugador"

    with col2:
        if st.button("ðŸŒï¸ Crear Ronda", use_container_width=True):
            st.session_state["page"] = "crear_ronda"

    if st.button("âœï¸ Modificar Ronda", use_container_width=True, key="btn_modificar_ronda"):
        st.session_state["page"] = "modificar_ronda"

    if st.button("Importar Ronda", use_container_width=True, key="btn_importar_ronda"):
        st.session_state["page"] = "importar_ronda"

    st.markdown("---")

    # PAGINA CREAR JUGADOR
    if st.session_state.get("page") == "crear_jugador":

        st.header("ðŸ‘¤ Nuevo Jugador")

        name = st.text_input("Nombre")
        email = st.text_input("Email")

        if st.button("Guardar Jugador"):





            try:

                    response = supabase.table("players").insert({
                        "name": name,
                        "email": email
                    }).execute()

                    st.success("Jugador creado")

            except Exception as e:
                    st.error(str(e))

    # PAGINA CREAR RONDA
    if st.session_state.get("page") == "crear_ronda":

        st.header("ðŸŒï¸ Nueva Ronda")




        # =========================
        # CARGAR CAMPOS
        # =========================
        courses = supabase.table("courses").select("*").execute().data

        course_options = {
            course["name"]: course["id"]
            for course in courses
        }

        selected_course_name = st.selectbox(
            "Selecciona el Campo",
            options=list(course_options.keys()),
            index=None,
            placeholder="Selecciona un campo..."
        )
        if selected_course_name is None:
            st.stop()
        selected_course_id = course_options[selected_course_name]

        # =========================
        # CARGAR TEES DEL CAMPO
        # =========================
        tees = supabase.table("tees") \
            .select("*") \
            .eq("course_id", selected_course_id) \
            .execute().data

        tee_options = {
            tee["color"]: tee["id"]
            for tee in tees
        }

        selected_tee_name = st.selectbox(
            "Selecciona las Tees",
            options=list(tee_options.keys()),
            index=None,
            placeholder="Selecciona las tees..."
        )
        if selected_tee_name is None:
            st.stop()
        selected_tee_id = tee_options[selected_tee_name]

        # OBTENER DATOS DE LA TEE SELECCIONADA
        selected_tee = next(
            tee for tee in tees
            if tee["id"] == selected_tee_id
        )

        slope_rating = selected_tee["slope"]
        course_rating = selected_tee["rating"]

        # =========================
        # FECHA DE LA RONDA
        # =========================
        round_date = st.date_input(
            "Fecha de la ronda",
            value=_dt_global.now(_TZ_CST).date()
        )

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
            list(player_options.keys()),
            index=None,
            placeholder="Selecciona un jugador..."
        )
        if selected_player_name is None:
            st.stop()

        # Obtener UUID del jugador seleccionado
        player_id = player_options[selected_player_name]

        # SCORES POR HOYO
        st.subheader("Front 9")
        front_cols = st.columns(9)
        front_scores_list = []
        for i, col in enumerate(front_cols):
            with col:
                v = st.number_input(f"H{i+1}", min_value=0, max_value=20, value=0, step=1, key=f"cr_f{i+1}")
                front_scores_list.append(v)

        st.subheader("Back 9")
        back_cols = st.columns(9)
        back_scores_list = []
        for i, col in enumerate(back_cols):
            with col:
                v = st.number_input(f"H{i+10}", min_value=0, max_value=20, value=0, step=1, key=f"cr_b{i+10}")
                back_scores_list.append(v)

        # Totales
        front_total = sum(front_scores_list)
        back_total = sum(back_scores_list)
        total = front_total + back_total

        st.markdown("---")

        st.write(f"Front: {front_total}")
        st.write(f"Back: {back_total}")
        st.write(f"Total: {total}")
        if st.button("Guardar Ronda"):
            round_id = str(uuid.uuid4())

            supabase.table("rounds").insert({
            "round_id": round_id,
            "player_id": player_id,
            "course_id": selected_course_id,
            "tee_id": selected_tee_id,
            "played_at": str(round_date),
            "total_score": int(total),
            }).execute()

            for i, strokes in enumerate(front_scores_list):
                supabase.table("round_holes").insert({
                    "round_id": round_id,
                    "hole_number": i + 1,
                    "strokes": int(strokes)
                }).execute()

            for i, strokes in enumerate(back_scores_list):
                supabase.table("round_holes").insert({
                    "round_id": round_id,
                    "hole_number": i + 10,
                    "strokes": int(strokes)
                }).execute()

            ###Calcular Total Ajustado
            adjusted_total = calcular_total_ajustado(
                supabase,
                selected_course_id,
                round_id,

            )
            
            ###Calcular Diferencial
            differential = calcular_differential(
            supabase,    
            adjusted_total,
            course_rating,
            round_id,
            slope_rating
            )

            ###Calcuar HDC del Jugador
            handicap_index = calcular_handicap_index(
            supabase,
            player_id
            )

            st.success("Ronda guardada")





    # PAGINA MODIFICAR RONDA
    if st.session_state.get("page") == "modificar_ronda":

        st.header("âœï¸ Modificar Ronda")

        players_mod = supabase.table("players").select("*").order("name").execute().data
        player_options_mod = {p["name"]: p["id"] for p in players_mod}

        selected_player_mod = st.selectbox("Jugador", list(player_options_mod.keys()), index=None, placeholder="Selecciona un jugador...", key="mod_player")
        if selected_player_mod is None:
            st.stop()
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

            # Cargar todos los campos y tees para editar
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

            # Fecha editable
            from datetime import date as _date, datetime as _datetime
            current_date = _datetime.strptime(selected_round["played_at"], "%Y-%m-%d").date() if selected_round.get("played_at") else _dt_global.now(_TZ_CST).date()
            new_date = st.date_input("Fecha de la ronda", value=current_date, key="mod_date")

            # Scores actuales
            holes_data = {
                h["hole_number"]: h["strokes"]
                for h in supabase.table("round_holes").select("*").eq("round_id", selected_round_id).execute().data
            }

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
            st.write(f"Front: {front_total_mod}")
            st.write(f"Back: {back_total_mod}")
            st.write(f"Total: {total_mod}")

            col_save, col_del = st.columns(2)

            with col_save:
                if st.button("ðŸ’¾ Guardar cambios", use_container_width=True):

                    supabase.table("rounds").update({
                        "total_score": int(total_mod),
                        "tee_id":      selected_tee_id_mod,
                        "course_id":   selected_course_id_mod,
                        "played_at":   str(new_date)
                    }).eq("round_id", selected_round_id).execute()

                    for _, row in pd.concat([front_mod, back_mod]).iterrows():
                        supabase.table("round_holes") \
                            .update({"strokes": int(row["Score"])}) \
                            .eq("round_id", selected_round_id) \
                            .eq("hole_number", int(row["Hoyo"])) \
                            .execute()

                    adjusted_total_mod = calcular_total_ajustado(supabase, selected_course_id_mod, selected_round_id)
                    differential_mod   = calcular_differential(supabase, adjusted_total_mod, tee_mod["rating"], selected_round_id, tee_mod["slope"])
                    handicap_mod       = calcular_handicap_index(supabase, player_id_mod)
                    hdc_str = str(handicap_mod) if handicap_mod is not None else "Sin datos suficientes"
                    st.success(f"Ronda actualizada. Diferencial: {differential_mod} | Handicap Index: {hdc_str}")

            with col_del:
                if st.button("ðŸ—‘ï¸ Borrar ronda", use_container_width=True, type="primary"):
                    st.session_state["confirm_delete"] = selected_round_id

            if st.session_state.get("confirm_delete") == selected_round_id:
                st.warning("âš ï¸ Â¿Seguro que quieres borrar esta ronda? Esta acciÃ³n no se puede deshacer.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("SÃ­, borrar", use_container_width=True):
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


    # PAGINA IMPORTAR RONDA
    if st.session_state.get("page") == "importar_ronda":

        st.header("Importar Ronda desde Torneo")

        try:
            all_torneos = supabase.table("tournaments").select("id, name, date, format").order("date", desc=True).execute().data or []
        except Exception as _et:
            st.error("Error cargando torneos: " + str(_et))
            all_torneos = []

        if not all_torneos:
            st.info("No hay torneos disponibles.")
            st.stop()

        torneo_labels = {}
        for t in all_torneos:
            lbl = str(t.get("date", "?")) + " - " + str(t.get("name", "?")) + " (" + str(t.get("format", "?")) + ")"
            torneo_labels[lbl] = t

        sel_torneo_label = st.selectbox("Selecciona un torneo", list(torneo_labels.keys()), index=None, placeholder="Selecciona un torneo...")
        if sel_torneo_label is None:
            st.stop()
        torneo = torneo_labels[sel_torneo_label]

        try:
            groups_imp = supabase.table("groups").select("id, name").eq("tournament_id", torneo["id"]).execute().data or []
        except Exception:
            groups_imp = []

        all_gp = []
        for grp in groups_imp:
            try:
                gps = supabase.table("group_players").select("id, player_id, guest_id, player_name").eq("group_id", grp["id"]).execute().data or []
                for gp in gps:
                    gp["group_name"] = grp["name"]
                    all_gp.append(gp)
            except Exception:
                pass

        if not all_gp:
            st.info("Este torneo no tiene jugadores registrados.")
            st.stop()

        try:
            scores_raw = supabase.table("tournament_scores").select("player_id, guest_id, hole_number, strokes").eq("tournament_id", torneo["id"]).execute().data or []
        except Exception:
            scores_raw = []

        scores_idx = {}
        for s in scores_raw:
            pid = s.get("player_id") or s.get("guest_id")
            scores_idx[(pid, int(s["hole_number"]))] = s["strokes"]

        st.markdown("---")
        st.subheader("Scores del torneo")
        tabla_rows = []
        for gp in all_gp:
            pid = gp.get("player_id") or gp.get("guest_id")
            row = {"Jugador": str(gp["player_name"]), "Grupo": str(gp["group_name"])}
            total_h = 0
            for h in range(1, 19):
                v = scores_idx.get((pid, h))
                row["H" + str(h)] = str(v) if v is not None else "-"
                if v:
                    total_h += v
            row["Total"] = str(total_h) if total_h else "-"
            tabla_rows.append(row)
        st.dataframe(pd.DataFrame(tabla_rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Seleccionar jugador para importar")

        gp_opts = {}
        for gp in all_gp:
            lbl = str(gp["player_name"]) + " (" + str(gp["group_name"]) + ")"
            gp_opts[lbl] = gp

        sel_gp_label = st.selectbox("Jugador del torneo", list(gp_opts.keys()), index=None, placeholder="Selecciona jugador...")
        if sel_gp_label is None:
            st.stop()
        sel_gp = gp_opts[sel_gp_label]

        try:
            players_hdc = supabase.table("players").select("id, name").order("name").execute().data or []
        except Exception:
            players_hdc = []
        phdc_opts = {p["name"]: p["id"] for p in players_hdc}

        sel_player_hdc = st.selectbox("Jugador en el sistema HDC", list(phdc_opts.keys()), index=None, placeholder="Selecciona jugador HDC...")
        if sel_player_hdc is None:
            st.stop()

        try:
            courses_imp = supabase.table("courses").select("id, name").execute().data or []
        except Exception:
            courses_imp = []
        cimp_opts = {c["name"]: c["id"] for c in courses_imp}

        sel_course_imp = st.selectbox("Campo", list(cimp_opts.keys()), index=None, placeholder="Selecciona campo...")
        if sel_course_imp is None:
            st.stop()
        _cid_imp = cimp_opts[sel_course_imp]

        try:
            tees_imp = supabase.table("tees").select("id, color, rating, slope").eq("course_id", _cid_imp).execute().data or []
            tee_imp_opts = {t["color"]: t for t in tees_imp}
        except Exception:
            tee_imp_opts = {}

        if not tee_imp_opts:
            st.info("No hay tees para este campo.")
            st.stop()

        sel_tee_imp = st.selectbox("Tees", list(tee_imp_opts.keys()), index=None, placeholder="Selecciona tees...")
        if sel_tee_imp is None:
            st.stop()
        _tee_imp = tee_imp_opts[sel_tee_imp]

        sel_date_imp = st.date_input("Fecha de la ronda", value=_dt_global.now(_TZ_CST).date(), key="imp_date")

        _pid_sel = sel_gp.get("player_id") or sel_gp.get("guest_id")
        front_scores_imp = [scores_idx.get((_pid_sel, h), 0) for h in range(1, 10)]
        back_scores_imp  = [scores_idx.get((_pid_sel, h), 0) for h in range(10, 19)]

        front_df_imp = pd.DataFrame({"Hoyo": list(range(1, 10)),  "Score": front_scores_imp})
        back_df_imp  = pd.DataFrame({"Hoyo": list(range(10, 19)), "Score": back_scores_imp})

        st.subheader("Front 9")
        front_edit_imp = st.data_editor(front_df_imp, hide_index=True, use_container_width=True, key="imp_front")
        st.subheader("Back 9")
        back_edit_imp  = st.data_editor(back_df_imp,  hide_index=True, use_container_width=True, key="imp_back")

        ft = int(front_edit_imp["Score"].sum())
        bt = int(back_edit_imp["Score"].sum())
        st.write("Front: " + str(ft) + " | Back: " + str(bt) + " | Total: " + str(ft + bt))

        if st.button("Importar Ronda", type="primary", use_container_width=True, key="btn_imp_final"):
            try:
                _pid_hdc = phdc_opts[sel_player_hdc]
                _rid_imp = str(uuid.uuid4())
                supabase.table("rounds").insert({
                    "round_id": _rid_imp,
                    "player_id": _pid_hdc,
                    "course_id": _cid_imp,
                    "tee_id": _tee_imp["id"],
                    "played_at": str(sel_date_imp),
                    "total_score": ft + bt,
                }).execute()
                for _, row in pd.concat([front_edit_imp, back_edit_imp]).iterrows():
                    supabase.table("round_holes").insert({
                        "round_id": _rid_imp,
                        "hole_number": int(row["Hoyo"]),
                        "strokes": int(row["Score"])
                    }).execute()
                _adj  = calcular_total_ajustado(supabase, _cid_imp, _rid_imp)
                _diff = calcular_differential(supabase, _adj, _tee_imp["rating"], _rid_imp, _tee_imp["slope"])
                _hdc  = calcular_handicap_index(supabase, _pid_hdc)
                st.success("Ronda importada. Diferencial: " + str(_diff) + " | HDC: " + str(_hdc))
            except Exception as _ei:
                st.error("Error al importar: " + str(_ei))
