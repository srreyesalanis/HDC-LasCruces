
import streamlit as st

st.set_page_config(
    page_title="Golf Handicap",
    page_icon="⛳",
    layout="centered"
)

st.title("⛳ Golf Handicap System")

st.markdown("---")

st.subheader("Menú Principal")

col1, col2 = st.columns(2)

with col1:
    if st.button("👤 Crear Jugador", use_container_width=True):
        st.session_state["page"] = "crear_jugador"

with col2:
    if st.button("🏌️ Crear Ronda", use_container_width=True):
        st.session_state["page"] = "crear_ronda"

st.markdown("---")

# PAGINA CREAR JUGADOR
if st.session_state.get("page") == "crear_jugador":

    st.header("👤 Nuevo Jugador")

    nombre = st.text_input("Nombre")
    email = st.text_input("Email")

    if st.button("Guardar Jugador"):

        from supabase import create_client

        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


        st.success(f"Jugador {nombre} creado correctamente")

# PAGINA CREAR RONDA
if st.session_state.get("page") == "crear_ronda":

    st.header("🏌️ Nueva Ronda")

    jugador = st.selectbox(
        "Jugador",
        ["Roberto", "Juan", "Pedro"]
    )

    hoyo = st.number_input(
        "Hoyo",
        min_value=1,
        max_value=18,
        step=1
    )

    golpes = st.number_input(
        "Golpes",
        min_value=1,
        max_value=15,
        step=1
    )

    if st.button("Guardar Ronda"):

        # AQUI VA TU INSERT A SUPABASE
        st.success("Ronda guardada correctamente")
```

## Resultado

La app mostrará:

* Botón "Crear Jugador"
* Botón "Crear Ronda"
* Formularios simples
* Navegación básica usando `session_state`

## Ejecutar localmente

```bash
streamlit run streamlit_app.py
```

## Siguiente mejora recomendada

Conectar los botones a Supabase usando:

```python
supabase.table("players").insert()
```

y:

```python
supabase.table("rounds").insert()
```
