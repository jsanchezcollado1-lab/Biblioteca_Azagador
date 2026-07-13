import streamlit as st
import pandas as pd
import unicodedata

st.set_page_config(page_title="Mi Biblioteca Virtual", page_icon="📚", layout="wide")

# Usamos directamente la URL de exportación pública que no requiere permisos de API de Google
URL_CSV = "https://docs.google.com/spreadsheets/d/1seARxKE_IvbGkQXZYgPWLmW-k34NsFIF/export?format=csv"

# Función para quitar tildes y hacer la búsqueda infalible
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Cargar los datos directamente desde el enlace CSV público
@st.cache_data(ttl=5)  # Se actualiza rápido
def cargar_datos():
    try:
        # Forzamos la lectura limpia del CSV de Google
        return pd.read_csv(URL_CSV)
    except Exception as e:
        st.error(f"Error al leer el documento de Google Sheets: {e}")
        return pd.DataFrame()

df = cargar_datos()

st.title("📚 Buscador y Gestor de Biblioteca")
st.write("Busca cualquier libro de tu colección en tiempo real.")

if df.empty:
    st.warning("No se pudieron cargar los libros. Revisa que el documento de Google Sheets esté compartido como 'Cualquier persona con el enlace'.")
else:
    columnas_reales = df.columns.tolist()
    
    # Buscador interactivo
    busqueda_usuario = st.text_input("🔍 Escribe el título, autor o letras del libro:", "")
    busqueda_normalizada = normalizar_texto(busqueda_usuario)

    if busqueda_normalizada:
        col_titulo = columnas_reales[0]
        col_autor = columnas_reales[1]
        masca_titulo = df[col_titulo].apply(normalizar_texto).str.contains(busqueda_normalizada, na=False)
        masca_autor = df[col_autor].apply(normalizar_texto).str.contains(busqueda_normalizada, na=False)
        df_filtrado = df[masca_titulo | masca_autor]
    else:
        df_filtrado = df

    st.subheader(f"Libros encontrados ({len(df_filtrado)})")

    if not df_filtrado.empty:
        for index, row in df_filtrado.iterrows():
            titulo_libro = row.iloc[0]
            autor_libro = row.iloc[1]
            lugar = row.iloc[2] if len(row) > 2 else "No especificado"
            donde = row.iloc[3] if len(row) > 3 else "No especificado"
            prestado_a = row.iloc[4] if len(row) > 4 and pd.notna(row.iloc[4]) else "Nadie (Disponible)"
            
            with st.expander(f"📖 {titulo_libro} — *{autor_libro}*"):
                st.markdown(f"📍 **Ubicación:** {lugar} — {donde}")
                st.markdown(f"👤 **Estado actual:** Prestado a {prestado_a}" if prestado_a != "Nadie (Disponible)" else "✅ **Estado actual:** Disponible en la estantería")
                
                # Explicación de edición debido a las restricciones del servidor
                st.caption("Nota: Para modificar a quién se le deja, edítalo directamente en la app de Google Sheets de tu móvil y los cambios aparecerán aquí al instante.")
                        
        st.markdown("---")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No se encontraron libros.")
