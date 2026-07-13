import streamlit as st
import pandas as pd
import os
import unicodedata

st.set_page_config(page_title="Biblioteca Azagador", page_icon="📚", layout="wide")

EXCEL_FILE = "inventario_libros.xlsx"

# Función para quitar tildes y hacer la búsqueda infalible
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    # Elimina acentos/tildes
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Cargar datos asegurando que no rompa la app
@st.cache_data(ttl=10)  
def cargar_datos():
    if os.path.exists(EXCEL_FILE):
        try:
            return pd.read_excel(EXCEL_FILE)
        except Exception as e:
            st.error(f"Error al abrir el Excel: {e}")
    return pd.DataFrame()

df = cargar_datos()

st.title("📚 Biblioteca COLLATUS TURIELIS")
st.write("Busca cualquier libro y registra a quién se lo has prestado.")

# Alerta si la base de datos está totalmente vacía
if df.empty:
    st.warning(f"⚠️ La base de datos está vacía. Verifica que el archivo '{EXCEL_FILE}' esté subido en la misma carpeta de GitHub y que tenga datos dentro.")
else:
    # Asegurar que existan las columnas clave en minúsculas para evitar errores de formato
    columnas_reales = df.columns.tolist()
    
    # Buscador interactivo
    busqueda_usuario = st.text_input("🔍 Escribe el título, autor o letras del libro:", "")
    busqueda_normalizada = normalizar_texto(busqueda_usuario)

    # Filtrado inteligente por coincidencias parciales y sin tildes
    if busqueda_normalizada:
        # Buscamos en la primera columna (Título) y segunda columna (Autor) dinámicamente
        col_titulo = columnas_reales[0]
        col_autor = columnas_reales[1]
        
        masca_titulo = df[col_titulo].apply(normalizar_texto).str.contains(busqueda_normalizada, na=False)
        masca_autor = df[col_autor].apply(normalizar_texto).str.contains(busqueda_normalizada, na=False)
        
        df_filtrado = df[masca_titulo | masca_autor]
    else:
        df_filtrado = df

    st.subheader(f"Libros encontrados ({len(df_filtrado)})")

    # Si hay libros, los muestra
    if not df_filtrado.empty:
        for index, row in df_filtrado.iterrows():
            titulo_libro = row.iloc[0]
            autor_libro = row.iloc[1]
            
            # Ubicaciones dinámicas basadas en tus columnas del Excel
            lugar = row.iloc[2] if len(row) > 2 else "No especificado"
            donde = row.iloc[3] if len(row) > 3 else "No especificado"
            
            with st.expander(f"📖 {titulo_libro} — *{autor_libro}*"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📍 **Ubicación:** {lugar} — {donde}")
                with col2:
                    # La columna de "Dejado a:" suele ser la quinta (índice 4) o la última
                    idx_dejado = 4 if len(row) > 4 else len(row) - 1
                    col_dejado_nombre = columnas_reales[idx_dejado]
                    
                    prestado_actual = str(row.iloc[idx_dejado]) if pd.notna(row.iloc[idx_dejado]) else ""
                    nuevo_prestamo = st.text_input("Dejado a:", value=prestado_actual, key=f"user_{index}")
                    
                    if st.button("💾 Guardar", key=f"btn_{index}"):
                        df.at[index, col_dejado_nombre] = nuevo_prestamo if nuevo_prestamo.strip() != "" else None
                        df.to_excel(EXCEL_FILE, index=False)
                        st.success("¡Préstamo registrado con éxito!")
                        st.clear_cache()
                        st.rerun()
                        
        st.markdown("---")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No se encontraron libros que coincidan con esas letras.")
