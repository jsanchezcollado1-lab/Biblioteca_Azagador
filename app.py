import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Mi Biblioteca Virtual", page_icon="📚", layout="wide")

EXCEL_FILE = "inventario_libros.xlsx"

# Función para cargar datos (con caché para que vaya rápido)
@st.cache_data(ttl=60)  # Se actualiza cada minuto si hay cambios
def cargar_datos():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    return pd.DataFrame(columns=["Título", "Autor", "Lugar", "Dónde", "Dejado a:"])

df = cargar_datos()

st.title("📚 Buscador y Gestor de Biblioteca")
st.write("Busca cualquier libro y registra a quién se lo has prestado.")

# Buscador en tiempo real
busqueda = st.text_input("🔍 Escribe el título o autor del libro:", "").lower()

if busqueda:
    df_filtrado = df[df["Título"].astype(str).str.lower().str.contains(busqueda) | df["Autor"].astype(str).str.lower().str.contains(busqueda)]
else:
    df_filtrado = df

st.subheader(f"Libros ({len(df_filtrado)})")

# Lista interactiva
for index, row in df_filtrado.iterrows():
    with st.expander(f"📖 {row['Título']} — {row['Autor']}"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"📍 **Ubicación:** {row['Lugar']} — {row['Dónde']}")
        with col2:
            prestado_actual = str(row['Dejado a:']) if pd.notna(row['Dejado a:']) else ""
            nuevo_prestamo = st.text_input("Dejado a:", value=prestado_actual, key=f"user_{index}")
            
            if st.button("💾 Guardar", key=f"btn_{index}"):
                # Modificamos el dataframe y guardamos en el Excel
                df.at[index, 'Dejado a:'] = nuevo_prestamo if nuevo_prestamo.strip() != "" else None
                df.to_excel(EXCEL_FILE, index=False)
                st.success("¡Prestamo registrado!")
                st.clear_cache() # Limpiamos caché para que todos vean el cambio
                st.rerun()

st.markdown("---")
st.dataframe(df, use_container_width=True)
