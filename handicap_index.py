def calcular_handicap_index(
    supabase,
    player_id
):
    """
    Calcula el Handicap Index usando
    los últimos 20 differentials.
    El número de rondas a promediar depende
    del total de rondas disponibles:
      8       → 2 mejores + 1.0
      9-11    → 3 mejores
      12-14   → 4 mejores
      15-16   → 5 mejores
      17-18   → 6 mejores
      19      → 7 mejores
      20      → 8 mejores
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
    n = len(rounds)
    if n < 8:
        return None

    # =========================
    # EXTRAER DIFFERENTIALS
    # =========================
    differentials = [
        float(r["differential"])
        for r in rounds
    ]

    # =========================
    # DETERMINAR CUANTAS USAR
    # =========================
    if n == 8:
        count = 2
        adjustment = 1.0
    elif n <= 11:
        count = 3
        adjustment = 0.0
    elif n <= 14:
        count = 4
        adjustment = 0.0
    elif n <= 16:
        count = 5
        adjustment = 0.0
    elif n <= 18:
        count = 6
        adjustment = 0.0
    elif n == 19:
        count = 7
        adjustment = 0.0
    else:  # 20
        count = 8
        adjustment = 0.0

    best = sorted(differentials)[:count]

    # =========================
    # CALCULAR PROMEDIO
    # =========================
    handicap_index = round(
        sum(best) / count + adjustment,
        1
    )

    # Cap máximo en 36
    handicap_index = min(handicap_index, 36.0)

    # =========================
    # ACTUALIZAR GOLFER
    # =========================
    supabase.table("players") \
        .update({
            "current_handicap": handicap_index
        }) \
        .eq("id", player_id) \
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