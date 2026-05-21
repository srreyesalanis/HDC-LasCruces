def calcular_differential(
    supabase,
    round_id,    
    adjusted_total,
    course_rating,
    slope_rating
):
    differential = (
        (adjusted_total - course_rating)
        * 113
    ) / slope_rating

    supabase.table("rounds") \
    .update({
    "differential": differential,
    "course_rating_used": course_rating,
    "slope_rating_used": slope_rating
    }) \
    .eq("round_id", round_id) \
    .execute()    

    return round(differential, 1)
