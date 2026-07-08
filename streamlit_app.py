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
        "Cerrar Sesion",
        type="primary",
        use_container_width=True,
        key="logout_button"
        )

        if logout_button:

            supabase.auth.sign_out()

            st.session_state.user = None

            st.rerun()

    st.markdown(f"Bienvenido **{st.session_state.user.email}**")
    st.markdown("---")

    tab_jugador, tab_ronda, tab_mod, tab_import = st.tabs(["Crear Jugador", "Crear Ronda", "Modificar Ronda", "Importar Ronda"])

    # PAGINA CREAR JUGADOR
    with tab_jugador:

        st.header("Nuevo Jugador")

        name      = st.text_input("Nombre", key="jug_nombre")
        email_jug = st.text_input("Email",  key="jug_email")

        if st.button("Guardar Jugador", key="btn_guardar_jug"):
            try:
                supabase.table("players").insert({"name": name, "email": email_jug}).execute()
                st.success("Jugador creado")
            except Exception:
                st.error("Error al guardar jugador.")

    with tab_ronda:

        st.header("Nueva Ronda")

        try:
            _crs = supabase.table("courses").select("*").execute().data or []
        except Exception:
            _crs = []
        course_options = {c["name"]: c["id"] for c in _crs}

        st.selectbox("Campo", list(course_options.keys()), index=None, placeholder="Selecciona un campo...", key="ronda_course")

        tee_options = {}
        if st.session_state.get("ronda_course") and course_options:
            try:
                _cid = course_options.get(st.session_state["ronda_course"])
                if _cid:
                    _td = supabase.table("tees").select("*").eq("course_id", _cid).execute().data or []
                    tee_options = {t["color"]: t for t in _td}
            except Exception:
                tee_options = {}

        _tk = list(tee_options.keys()) if tee_options else [""]
        st.selectbox("Tees", _tk, index=None if tee_options else 0, placeholder="Tees...", key="ronda_tee")

        try:
            _pls = supabase.table("players").select("*").order("name").execute().data or []
        except Exception:
            _pls = []
        player_options = {p["name"]: p["id"] for p in _pls}

        st.selectbox("Jugador", list(player_options.keys()), index=None, placeholder="Selecciona un jugador...", key="ronda_player")
        round_date = st.date_input("Fecha de la ronda", value=_dt_global.now(_TZ_CST).date(), key="ronda_date")

        st.subheader("Front 9")
        front_scores = st.data_editor(pd.DataFrame({"Hoyo": list(range(1,10)),  "Score": [0]*9}), hide_index=True, use_container_width=True, key="ronda_front")
        st.subheader("Back 9")
        back_scores  = st.data_editor(pd.DataFrame({"Hoyo": list(range(10,19)), "Score": [0]*9}), hide_index=True, use_container_width=True, key="ronda_back")

        front_total = front_scores["Score"].sum()
        back_total  = back_scores["Score"].sum()
        total = front_total + back_total
        st.write(f"Front: {front_total} | Back: {back_total} | Total: {total}")

        if st.button("Guardar Ronda", key="btn_guardar_ronda", use_container_width=True, type="primary"):
            _pn = st.session_state.get("ronda_player")
            _cn = st.session_state.get("ronda_course")
            _tn = st.session_state.get("ronda_tee")
            if not _pn or not _cn or not _tn:
                st.error("Selecciona campo, tees y jugador.")
            else:
                try:
                    _tee = tee_options.get(_tn)
                    if not _tee:
                        st.error("Tee no encontrado.")
                    else:
                        _pid  = player_options[_pn]
                        _cid2 = course_options[_cn]
                        _rid  = str(uuid.uuid4())
                        supabase.table("rounds").insert({"round_id": _rid, "player_id": _pid, "course_id": _cid2, "tee_id": _tee["id"], "played_at": str(round_date), "total_score": int(total)}).execute()
                        for _, row in pd.concat([front_scores, back_scores]).iterrows():
                            supabase.table("round_holes").insert({"round_id": _rid, "hole_number": int(row["Hoyo"]), "strokes": int(row["Score"])}).execute()
                        _adj  = calcular_total_ajustado(supabase, _cid2, _rid)
                        _diff = calcular_differential(supabase, _adj, _tee["rating"], _rid, _tee["slope"])
                        _hdc  = calcular_handicap_index(supabase, _pid)
                        st.success("Ronda guardada")
                except Exception:
                    st.error("Error al guardar ronda.")

    with tab_mod:

        st.header("Modificar Ronda")

        try:
            _pmod = supabase.table("players").select("*").order("name").execute().data or []
        except Exception:
            _pmod = []
        popts_mod = {p["name"]: p["id"] for p in _pmod}

        st.selectbox("Jugador", list(popts_mod.keys()), index=None, placeholder="Selecciona un jugador...", key="mod_player")

        _pid_mod = popts_mod.get(st.session_state.get("mod_player", ""))
        rounds_data = []
        if _pid_mod:
            try:
                rounds_data = supabase.table("rounds").select("*").eq("player_id", _pid_mod).order("played_at", desc=True).execute().data or []
            except Exception:
                rounds_data = []

        def _rlabel(r):
            diff = r.get("differential", "N/A")
            return f"{r['played_at']} - Total: {r['total_score']} | Dif: {diff}"

        round_opts_mod = {_rlabel(r): r["round_id"] for r in rounds_data} if rounds_data else {}
        _round_keys = list(round_opts_mod.keys()) if round_opts_mod else []
        st.selectbox("Ronda", _round_keys, index=None, placeholder="Selecciona una ronda...", key="mod_round")

        _rid_mod = round_opts_mod.get(st.session_state.get("mod_round", ""))
        _sel_round = next((r for r in rounds_data if r.get("round_id") == _rid_mod), None) if _rid_mod else None

        try:
            _cmod = supabase.table("courses").select("*").execute().data or []
        except Exception:
            _cmod = []
        copts_mod = {c["name"]: c["id"] for c in _cmod}
        _cur_course = next((c["name"] for c in _cmod if _sel_round and c["id"] == _sel_round.get("course_id")), None)
        _cidx_mod = list(copts_mod.keys()).index(_cur_course) if _cur_course and _cur_course in copts_mod else None
        st.selectbox("Campo", list(copts_mod.keys()), index=_cidx_mod, placeholder="Campo...", key="mod_course")

        _cid_mod = copts_mod.get(st.session_state.get("mod_course", ""))
        tee_list_mod = []
        if _cid_mod:
            try:
                tee_list_mod = supabase.table("tees").select("*").eq("course_id", _cid_mod).execute().data or []
            except Exception:
                tee_list_mod = []
        topts_mod = {t["color"]: t for t in tee_list_mod}
        _cur_tee = next((t["color"] for t in tee_list_mod if _sel_round and t["id"] == _sel_round.get("tee_id")), None)
        _tidx_mod = list(topts_mod.keys()).index(_cur_tee) if _cur_tee and _cur_tee in topts_mod else None
        st.selectbox("Tees", list(topts_mod.keys()), index=_tidx_mod, placeholder="Tees...", key="mod_tee")

        from datetime import datetime as _dtmod
        _cur_date_mod = _dtmod.strptime(_sel_round["played_at"], "%Y-%m-%d").date() if _sel_round and _sel_round.get("played_at") else _dt_global.now(_TZ_CST).date()
        st.date_input("Fecha", value=_cur_date_mod, key="mod_date")

        _holes_mod = {}
        if _rid_mod:
            try:
                _hd = supabase.table("round_holes").select("*").eq("round_id", _rid_mod).execute().data or []
                _holes_mod = {h["hole_number"]: h["strokes"] for h in _hd}
            except Exception:
                _holes_mod = {}

        _fdf = pd.DataFrame({"Hoyo": list(range(1, 10)),  "Score": [_holes_mod.get(h, 0) for h in range(1, 10)]})
        _bdf = pd.DataFrame({"Hoyo": list(range(10, 19)), "Score": [_holes_mod.get(h, 0) for h in range(10, 19)]})

        st.subheader("Front 9")
        front_mod = st.data_editor(_fdf, hide_index=True, use_container_width=True, key="mod_front")
        st.subheader("Back 9")
        back_mod  = st.data_editor(_bdf, hide_index=True, use_container_width=True, key="mod_back")

        ft_mod = front_mod["Score"].sum()
        bt_mod = back_mod["Score"].sum()
        tt_mod = ft_mod + bt_mod
        st.write(f"Front: {ft_mod} | Back: {bt_mod} | Total: {tt_mod}")
        st.markdown("---")

        col_save, col_del = st.columns(2)
        with col_save:
            if st.button("Guardar cambios", use_container_width=True, key="mod_btn_save"):
                if not _rid_mod or not _pid_mod:
                    st.error("Selecciona jugador y ronda.")
                else:
                    try:
                        _tid_mod = topts_mod.get(st.session_state.get("mod_tee", ""), {}).get("id")
                        supabase.table("rounds").update({"total_score": int(tt_mod), "tee_id": _tid_mod, "course_id": _cid_mod, "played_at": str(st.session_state["mod_date"])}).eq("round_id", _rid_mod).execute()
                        for _, row in pd.concat([front_mod, back_mod]).iterrows():
                            supabase.table("round_holes").update({"strokes": int(row["Score"])}).eq("round_id", _rid_mod).eq("hole_number", int(row["Hoyo"])).execute()
                        _adj_mod = calcular_total_ajustado(supabase, _cid_mod, _rid_mod)
                        _tee_mod = topts_mod.get(st.session_state.get("mod_tee", ""), {})
                        _diff_mod = calcular_differential(supabase, _adj_mod, _tee_mod.get("rating"), _rid_mod, _tee_mod.get("slope"))
                        _hdc_mod = calcular_handicap_index(supabase, _pid_mod)
                        st.success(f"Ronda actualizada. Dif: {_diff_mod} | HDC: {_hdc_mod}")
                    except Exception as _e:
                        st.error(f"Error al guardar: {_e}")
        with col_del:
            if st.button("Borrar ronda", use_container_width=True, type="primary", key="mod_btn_del"):
                if _rid_mod:
                    st.session_state["confirm_delete"] = _rid_mod

        if _rid_mod and st.session_state.get("confirm_delete") == _rid_mod:
            st.warning("Seguro que quieres borrar esta ronda? Esta accion no se puede deshacer.")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Si, borrar", use_container_width=True, key="mod_btn_yes"):
                    try:
                        supabase.table("round_holes").delete().eq("round_id", _rid_mod).execute()
                        supabase.table("rounds").delete().eq("round_id", _rid_mod).execute()
                        calcular_handicap_index(supabase, _pid_mod)
                        st.session_state["confirm_delete"] = None
                        st.success("Ronda eliminada.")
                        st.rerun()
                    except Exception as _e:
                        st.error(f"Error al borrar: {_e}")
            with col_no:
                if st.button("Cancelar", use_container_width=True, key="mod_btn_no"):
                    st.session_state["confirm_delete"] = None
                    st.rerun()

    with tab_import:

        st.header("Importar Ronda desde Torneo")

        try:
            all_torneos = supabase.table("tournaments").select("id, name, date, format").order("date", desc=True).execute().data or []
        except Exception:
            all_torneos = []

        torneo_labels = {f"{t['date']} - {t['name']} ({t.get('format', '?')})" : t for t in all_torneos}
        if not all_torneos:
            st.info("No hay torneos disponibles.")
        else:
            st.selectbox("Selecciona un torneo", list(torneo_labels.keys()), index=None, placeholder="Selecciona un torneo...", key="imp_torneo")

        _tlabel = st.session_state.get("imp_torneo")
        torneo = torneo_labels.get(_tlabel) if _tlabel else None

        all_gp = []
        scores_idx = {}
        if torneo:
            try:
                groups_imp = supabase.table("groups").select("id, name").eq("tournament_id", torneo["id"]).execute().data or []
                for grp in groups_imp:
                    gps = supabase.table("group_players").select("id, player_id, guest_id, player_name").eq("group_id", grp["id"]).execute().data or []
                    for gp in gps:
                        gp["group_name"] = grp["name"]
                        all_gp.append(gp)
                scores_raw = supabase.table("tournament_scores").select("player_id, guest_id, hole_number, strokes").eq("tournament_id", torneo["id"]).execute().data or []
                for s in scores_raw:
                    pid = s.get("player_id") or s.get("guest_id")
                    scores_idx[(pid, s["hole_number"])] = s["strokes"]
            except Exception as _e:
                st.error(f"Error cargando torneo: {_e}")

        if torneo and all_gp:
            st.markdown("---")
            st.subheader("Scores hoyo por hoyo")
            hoyos = list(range(1, 19))
            tabla_rows = []
            for gp in all_gp:
                pid = gp.get("player_id") or gp.get("guest_id")
                row = {"Jugador": gp["player_name"], "Grupo": gp["group_name"]}
                total = 0
                for h in hoyos:
                    v = scores_idx.get((pid, h))
                    row[f"H{h}"] = v if v is not None else "-"
                    if v: total += v
                row["Total"] = total if total else "-"
                tabla_rows.append(row)
            st.dataframe(pd.DataFrame(tabla_rows), use_container_width=True, hide_index=True)

        if torneo and all_gp:
            st.markdown("---")
            st.subheader("Importar jugador")

            try:
                players_hdc = supabase.table("players").select("id, name").order("name").execute().data or []
            except Exception:
                players_hdc = []
            phdc_opts = {p["name"]: p["id"] for p in players_hdc}

            try:
                courses_imp = supabase.table("courses").select("id, name").execute().data or []
            except Exception:
                courses_imp = []
            cimp_opts = {c["name"]: c["id"] for c in courses_imp}

            gp_opts = {f"{gp['player_name']} (Grupo: {gp['group_name']})": gp for gp in all_gp}
            st.selectbox("Jugador del torneo a importar", list(gp_opts.keys()), index=None, placeholder="Selecciona un jugador...", key="imp_gp")
            st.selectbox("Jugador en HDC Las Cruces", list(phdc_opts.keys()), index=None, placeholder="Selecciona jugador HDC...", key="imp_hdc_player")
            st.selectbox("Campo", list(cimp_opts.keys()), index=None, placeholder="Selecciona campo...", key="imp_course")

            _cname_imp = st.session_state.get("imp_course")
            _cid_imp = cimp_opts.get(_cname_imp) if _cname_imp else None
            tee_imp_opts = {}
            if _cid_imp:
                try:
                    tees_imp = supabase.table("tees").select("id, color, rating, slope").eq("course_id", _cid_imp).execute().data or []
                    tee_imp_opts = {t["color"]: t for t in tees_imp}
                except Exception:
                    tee_imp_opts = {}

            _timp_keys = list(tee_imp_opts.keys()) if tee_imp_opts else [""]
            st.selectbox("Tees", _timp_keys, index=None if tee_imp_opts else 0, placeholder="Tees...", key="imp_tee")
            st.date_input("Fecha de la ronda", value=_dt_global.now(_TZ_CST).date(), key="imp_date")

            _gp_label = st.session_state.get("imp_gp")
            _gp_sel = gp_opts.get(_gp_label) if _gp_label else None
            _pid_sel = (_gp_sel.get("player_id") or _gp_sel.get("guest_id")) if _gp_sel else None

            _fimp = pd.DataFrame({"Hoyo": list(range(1, 10)),  "Score": [scores_idx.get((_pid_sel, h), 0) for h in range(1, 10)]})
            _bimp = pd.DataFrame({"Hoyo": list(range(10, 19)), "Score": [scores_idx.get((_pid_sel, h), 0) for h in range(10, 19)]})

            st.subheader("Front 9")
            fimp_ed = st.data_editor(_fimp, hide_index=True, use_container_width=True, key="imp_front")
            st.subheader("Back 9")
            bimp_ed = st.data_editor(_bimp, hide_index=True, use_container_width=True, key="imp_back")

            ft_imp = fimp_ed["Score"].sum()
            bt_imp = bimp_ed["Score"].sum()
            tt_imp = ft_imp + bt_imp
            st.write(f"Front: {ft_imp} | Back: {bt_imp} | Total: {tt_imp}")

            if st.button("Importar ronda", use_container_width=True, key="btn_importar", type="primary"):
                _phdc_sel = st.session_state.get("imp_hdc_player")
                _tname_imp = st.session_state.get("imp_tee")
                if not _phdc_sel:
                    st.error("Selecciona el jugador HDC.")
                elif not _cid_imp or not _tname_imp or not _tname_imp in tee_imp_opts:
                    st.error("Selecciona campo y tees.")
                else:
                    try:
                        _tee_imp = tee_imp_opts[_tname_imp]
                        _phdc_id = phdc_opts[_phdc_sel]
                        _rid_imp = str(uuid.uuid4())
                        supabase.table("rounds").insert({"round_id": _rid_imp, "player_id": _phdc_id, "course_id": _cid_imp, "tee_id": _tee_imp["id"], "played_at": str(st.session_state["imp_date"]), "total_score": int(tt_imp)}).execute()
                        for _, row in pd.concat([fimp_ed, bimp_ed]).iterrows():
                            supabase.table("round_holes").insert({"round_id": _rid_imp, "hole_number": int(row["Hoyo"]), "strokes": int(row["Score"])}).execute()
                        _adj_imp = calcular_total_ajustado(supabase, _cid_imp, _rid_imp)
                        _diff_imp = calcular_differential(supabase, _adj_imp, _tee_imp["rating"], _rid_imp, _tee_imp["slope"])
                        _hdc_imp = calcular_handicap_index(supabase, _phdc_id)
                        _hs = str(_hdc_imp) if _hdc_imp is not None else "Sin datos"
                        st.success(f"Ronda importada. Dif: {_diff_imp} | HDC: {_hs}")
                    except Exception as _e:
                        st.error(f"Error al importar: {_e}")

