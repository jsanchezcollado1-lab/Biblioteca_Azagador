import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import unicodedata

st.set_page_config(page_title="Mi Biblioteca Virtual", page_icon="📚", layout="wide")

# Conexión mágica con Google Sheets utilizando los secretos guardados
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Forzamos ttl=0 para que siempre lea los datos más recientes en tiempo real
    df = conn.read(ttl=0)
except Exception as e:
    st.error(f"Error de conexión con Google Sheets: {e}")
    st.info("Revisa que hayas creado el archivo '.streamlit/secrets.toml' correctamente con el enlace de tu documento.")
    st.stop()

# Función para quitar tildes y hacer la búsqueda infalible
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

st.title("📚 Buscador y Gestor de Biblioteca")
st.write("Busca cualquier libro y registra a quién se lo has prestado en tiempo real.")

if df.empty:
    st.warning("La hoja de cálculo parece estar vacía o no se puede leer.")
else:
    columnas_reales = df.columns.tolist()
    
    # Buscador interactivo
    busqueda_usuario = st.text_input("🔍 Escribe el título, autor o letras del libro:", "")
    busqueda_normalizada = normalizar_texto(busqueda_usuario)

    # Filtrado inteligente por coincidencias parciales y sin tildes
    if busqueda_normalizada:
        col_titulo = columnas_reales[0]
        col_autor = columnas_reales[1]
        masca_titulo = df[col_titulo].apply(normalizar_texto).str.contains(busqueda_normalizada, na=False)
        masca_autor = df[col_autor].apply(normalizar_texto).str.contains(busqueda_normalizada, na=False)
        df_filtrado = df[masca_titulo | masca_autor]
    else:
        df_filtrado = df

    st.subheader(f"Libros encontrados ({len(df_filtrado)})")

    # Mostrar la lista interactiva
    if not df_filtrado.empty:
        for index, row in df_filtrado.iterrows():
            titulo_libro = row.iloc[0]
            autor_libro = row.iloc[1]
            lugar = row.iloc[2] if len(row) > 2 else "No especificado"
            donde = row.iloc[3] if len(row) > 3 else "No especificado"
            
            with st.expander(f"📖 {titulo_libro} — *{autor_libro}*"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📍 **Ubicación:** {lugar} — {donde}")
                with col2:
                    # Identificar la columna 'Dejado a:' (asumimos que es la quinta, índice 4)
                    idx_dejado = 4 if len(columnas_reales) > 4 else len(columnas_reales) - 1
                    col_dejado_nombre = columnas_reales[idx_dejado]
                    
                    prestado_actual = str(row.iloc[idx_dejado]) if pd.notna(row.iloc[idx_dejado]) else ""
                    nuevo_prestamo = st.text_input("Dejado a:", value=prestado_actual, key=f"user_{index}")
                    
                    if st.button("💾 Guardar en la Nube", key=f"btn_{index}"):
                        # Modificamos el valor localmente
                        df.at[index, col_dejado_nombre] = nuevo_prestamo if nuevo_prestamo.strip() != "" else None
                        
                        # Guardamos directamente de vuelta en Google Sheets de forma segura
                        try:
                            conn.update(data=df)
                            st.success(f"¡Préstamo de '{titulo_libro}' guardado en Google Sheets!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"No se pudo escribir en Google Sheets: {err}")
                            st.info("Asegúrate de que el documento no esté bloqueado o compartido sin permisos de edición.")
                        
        st.markdown("---")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No se encontraron libros.")
