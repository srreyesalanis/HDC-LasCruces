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

    # LOGOUT ARRIBA DERECHA
    top_col1, top_col2 = st.columns([8, 1])

    with top_col2:

        logout_button = st.button(
        "Cerrar Sesión",
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

    tab_jugador, tab_ronda, tab_mod, tab_import = st.tabs(["👤 Crear Jugador", "🏌️ Crear Ronda", "✏️ Modificar Ronda", "📥 Importar Ronda"])

    # PAGINA CREAR JUGADOR
    with tab_jugador:

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

            except Exception as e:
                    st.error(str(e))

    # PAGINA CREAR RONDA
    with tab_ronda:

        st.header("🏌️ Nueva Ronda")

        from supabase import create_client

        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
            round_id = str(uuid.uuid4())

            supabase.table("rounds").insert({
            "round_id": round_id,
            "player_id": player_id,
            "course_id": selected_course_id,
            "tee_id": selected_tee_id,
            "played_at": str(round_date),
            "total_score": int(total),
            }).execute()

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
    with tab_mod:

        st.header("✏️ Modificar Ronda")

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
                if st.button("💾 Guardar cambios", use_container_width=True):

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
                if st.button("🗑️ Borrar ronda", use_container_width=True, type="primary"):
                    st.session_state["confirm_delete"] = selected_round_id

            if st.session_state.get("confirm_delete") == selected_round_id:
                st.warning("⚠️ ¿Seguro que quieres borrar esta ronda? Esta acción no se puede deshacer.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Sí, borrar", use_container_width=True):
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
    with tab_import:
        st.header("📥 Importar Ronda desde Torneo")

        # Cargar torneos (Stableford + Bola Baja) del mismo Supabase
        all_torneos = supabase.table("tournaments").select("id, name, date, format").order("date", desc=True).limit(50).execute().data

        if not all_torneos:
            st.info("No hay torneos disponibles.")
        else:
            torneo_labels = {
                f"{t['date']} — {t['name']} ({t.get('format','?')})": t
                for t in all_torneos
            }
            selected_torneo_label = st.selectbox(
                "Selecciona un torneo",
                list(torneo_labels.keys()),
                index=None,
                placeholder="Selecciona un torneo...",
                key="imp_torneo"
            )

            if selected_torneo_label:
                torneo = torneo_labels[selected_torneo_label]
                torneo_id = torneo["id"]

                # Cargar grupos y jugadores del torneo
                groups_imp = supabase.table("groups").select("id, name").eq("tournament_id", torneo_id).execute().data
                all_gp = []
                for grp in groups_imp:
                    gps = supabase.table("group_players").select("id, player_id, guest_id, player_name, course_handicap").eq("group_id", grp["id"]).execute().data
                    for gp in gps:
                        gp["group_name"] = grp["name"]
                        all_gp.append(gp)

                if not all_gp:
                    st.warning("Este torneo no tiene jugadores registrados.")
                else:
                    # Cargar scores del torneo
                    scores_imp = supabase.table("tournament_scores").select("player_id, guest_id, hole_number, strokes, group_id").eq("tournament_id", torneo_id).execute().data

                    # Indice: (player_id o guest_id, hole_number) -> strokes
                    scores_idx = {}
                    for s in scores_imp:
                        pid = s.get("player_id") or s.get("guest_id")
                        scores_idx[(pid, s["hole_number"])] = s["strokes"]

                    st.markdown("---")
                    st.subheader("🔍 Scores hoyo por hoyo")

                    # Tabla resumen
                    hoyos = list(range(1, 19))
                    tabla_rows = []
                    for gp in all_gp:
                        pid = gp.get("player_id") or gp.get("guest_id")
                        row = {"Jugador": gp["player_name"], "Grupo": gp["group_name"], "HDC": gp.get("course_handicap", "-")}
                        total = 0
                        for h in hoyos:
                            v = scores_idx.get((pid, h))
                            row[f"H{h}"] = v if v is not None else "-"
                            if v: total += v
                        row["Total"] = total if total else "-"
                        tabla_rows.append(row)

                    df_imp = pd.DataFrame(tabla_rows)
                    st.dataframe(df_imp, use_container_width=True, hide_index=True)

                    st.markdown("---")
                    st.subheader("📤 Importar jugador")

                    # Cargar jugadores registrados en HDC
                    players_hdc = supabase.table("players").select("id, name").order("name").execute().data
                    player_hdc_opts = {p["name"]: p["id"] for p in players_hdc}

                    # Cargar cursos y tees
                    courses_imp = supabase.table("courses").select("id, name").execute().data
                    course_imp_opts = {c["name"]: c["id"] for c in courses_imp}

                    # Seleccionar jugador del torneo a importar
                    gp_opts = {f"{gp['player_name']} (Grupo: {gp['group_name']})": gp for gp in all_gp}
                    selected_gp_label = st.selectbox(
                        "Jugador del torneo a importar",
                        list(gp_opts.keys()),
                        index=None,
                        placeholder="Selecciona un jugador...",
                        key="imp_gp"
                    )

                    if selected_gp_label:
                        gp_sel = gp_opts[selected_gp_label]
                        pid_sel = gp_sel.get("player_id") or gp_sel.get("guest_id")

                        # Mapear a jugador HDC
                        player_hdc_sel = st.selectbox(
                            "Jugador en HDC Las Cruces",
                            list(player_hdc_opts.keys()),
                            index=None,
                            placeholder="Selecciona jugador HDC...",
                            key="imp_hdc_player"
                        )

                        # Campo y tee
                        course_sel_name = st.selectbox("Campo", list(course_imp_opts.keys()), index=None, placeholder="Campo...", key="imp_course")
                        if course_sel_name:
                            course_sel_id = course_imp_opts[course_sel_name]
                            tees_sel = supabase.table("tees").select("id, color, rating, slope").eq("course_id", course_sel_id).execute().data
                            tee_imp_opts = {t["color"]: t for t in tees_sel}
                            tee_sel_name = st.selectbox("Tees", list(tee_imp_opts.keys()), index=None, placeholder="Tees...", key="imp_tee")
                        else:
                            course_sel_id = None; tee_imp_opts = {}; tee_sel_name = None

                        # Fecha
                        imp_date = st.date_input("Fecha de la ronda", value=_dt_global.now(_TZ_CST).date(), key="imp_date")

                        # Scores editables del jugador seleccionado
                        front_imp = pd.DataFrame({
                            "Hoyo": list(range(1, 10)),
                            "Score": [scores_idx.get((pid_sel, h)) or 0 for h in range(1, 10)]
                        })
                        back_imp = pd.DataFrame({
                            "Hoyo": list(range(10, 19)),
                            "Score": [scores_idx.get((pid_sel, h)) or 0 for h in range(10, 19)]
                        })

                        st.subheader("Front 9")
                        front_imp_ed = st.data_editor(front_imp, hide_index=True, use_container_width=True, key="imp_front")
                        st.subheader("Back 9")
                        back_imp_ed  = st.data_editor(back_imp,  hide_index=True, use_container_width=True, key="imp_back")

                        front_t = front_imp_ed["Score"].sum()
                        back_t  = back_imp_ed["Score"].sum()
                        total_t = front_t + back_t
                        st.write(f"Front: {front_t} | Back: {back_t} | Total: {total_t}")

                        if st.button("📥 Importar ronda", use_container_width=True, key="btn_importar", type="primary"):
                            if not player_hdc_sel:
                                st.error("Selecciona el jugador HDC.")
                            elif not course_sel_id or not tee_sel_name:
                                st.error("Selecciona campo y tees.")
                            else:
                                tee_imp = tee_imp_opts[tee_sel_name]
                                player_hdc_id = player_hdc_opts[player_hdc_sel]
                                round_id_imp = str(uuid.uuid4())

                                supabase.table("rounds").insert({
                                    "round_id": round_id_imp,
                                    "player_id": player_hdc_id,
                                    "course_id": course_sel_id,
                                    "tee_id": tee_imp["id"],
                                    "played_at": str(imp_date),
                                    "total_score": int(total_t),
                                }).execute()

                                for _, row in pd.concat([front_imp_ed, back_imp_ed]).iterrows():
                                    supabase.table("round_holes").insert({
                                        "round_id": round_id_imp,
                                        "hole_number": int(row["Hoyo"]),
                                        "strokes": int(row["Score"])
                                    }).execute()

                                adjusted = calcular_total_ajustado(supabase, course_sel_id, round_id_imp)
                                differential = calcular_differential(supabase, adjusted, tee_imp["rating"], round_id_imp, tee_imp["slope"])
                                handicap_index = calcular_handicap_index(supabase, player_hdc_id)
                                hdc_str = str(handicap_index) if handicap_index is not None else "Sin datos suficientes"
                                st.success(f"✅ Ronda importada. Diferencial: {differential} | Handicap Index: {hdc_str}")

