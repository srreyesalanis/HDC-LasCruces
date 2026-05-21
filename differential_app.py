def calcular_differential(
    adjusted_score,
    course_rating,
    slope_rating
):
    differential = (
        (adjusted_score - course_rating)
        * 113
    ) / slope_rating

    return round(differential, 1)
