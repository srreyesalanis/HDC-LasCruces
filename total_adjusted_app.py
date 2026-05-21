def calcular_total_ajustado(
    supabase,
    course_id,
    round_id
):

    holes = supabase.table("holes") \
        .select("*") \
        .eq("course_id", course_id) \
        .order("hole_number") \
        .execute().data

    par_dict = {
        hole["hole_number"]: hole["par"]
        for hole in holes
    }

    round_scores = supabase.table("round_holes") \
        .select("*") \
        .eq("round_id", round_id) \
        .execute().data

    adjusted_total = 0

    for row in round_scores:

        hole = int(row["hole_number"])
        score = int(row["strokes"])

        par = par_dict[hole]

        adjusted_score = min(score, par + 3)

        adjusted_total += adjusted_score


    supabase.table("rounds") \
    .update({
    "total_adjusted": adjusted_total
    }) \
    .eq("round_id", round_id) \
    .execute()

    return adjusted_total