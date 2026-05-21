def calcular_differential(
    adjusted_total,
    course_rating,
    slope_rating
):
    differential = (
        (adjusted_total - course_rating)
        * 113
    ) / slope_rating

    return round(differential, 1)
