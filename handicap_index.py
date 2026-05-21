def calcular_handicap_index(
    supabase,
    player_id
):
    """
    Calcula el Handicap Index usando
    los últimos 20 differentials
    y tomando los mejores 8.
    """

    # =========================
    # OBTENER DIFFERENTIALS
    # =========================
    response = supabase.table("rounds") \
        .select("differential") \
        .eq("player_id", player_id) \
        .not_.is_("differential", "null") \
        .order("created_at", desc=True) \
        .limit(20) \
        .execute()

    rounds = response.data

    # =========================
    # VALIDAR RONDAS
    # =========================
    if len(rounds) < 8:
        return None

    # =========================
    # EXTRAER DIFFERENTIALS
    # =========================
    differentials = [
        float(round["differential"])
        for round in rounds
    ]

    # =========================
    # TOMAR MEJORES 8
    # =========================
    best_8 = sorted(differentials)[:8]

    # =========================
    # CALCULAR PROMEDIO
    # =========================
    handicap_index = round(
        sum(best_8) / 8,
        1
    )

    # =========================
    # ACTUALIZAR GOLFER
    # =========================
    supabase.table("players") \
        .update({
            "current_handicap": handicap_index
        }) \
        .eq("player_id", player_id) \
        .execute()

    # =========================
    # GUARDAR HISTORIAL
    # =========================
    supabase.table("handicaps") \
        .insert({
            "player_id": player_id,
            "handicap_index": handicap_index
        }) \
        .execute()

    return handicap_index