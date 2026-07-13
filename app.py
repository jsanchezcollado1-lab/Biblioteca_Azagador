import streamlit as st
import pandas as pd
import os
import unicodedata

st.set_page_config(page_title="Mi Biblioteca Virtual", page_icon="📚", layout="wide")

# URL de lectura pública de tu Google Sheets (Exportado a CSV)
URL_CSV = "https://docs.google.com/spreadsheets/d/1seARxKE_IvbGkQXZYgPWLmW-k34NsFIF/export?format=csv"
ARCHIVO_PRESTAMOS = "registro_prestamos.csv"

def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Cargar la base de datos de manera limpia y sin errores visuales
def cargar_biblioteca():
    try:
        df_libros = pd.read_csv(URL_CSV)
    except Exception:
        st.error("No se pudo leer la lista de Google Sheets. Asegúrate de que el documento siga compartido como 'Cualquier persona con el enlace'.")
        return pd.DataFrame()
        
    # Cargamos el archivo de préstamos de forma segura si existe
    if os.path.exists(ARCHIVO_PRESTAMOS):
        try:
            df_prestamos = pd.read_csv(ARCHIVO_PRESTAMOS, index_col="Titulo")
        except Exception:
            df_prestamos = pd.DataFrame(columns=["PrestadoA"])
            df_prestamos.index.name = "Titulo"
    else:
        # Si no existe, creamos una estructura vacía en memoria silenciosamente
        df_prestamos = pd.DataFrame(columns=["PrestadoA"])
        df_prestamos.index.name = "Titulo"
        
    # Combinar de forma segura los libros con los nombres de los préstamos
    df_libros["Dejado a:"] = df_libros.iloc[:, 0].map(df_prestamos["PrestadoA"]).fillna("")
    return df_libros

df = cargar_biblioteca()

st.title("📚 Buscador y Gestor de Biblioteca")
st.write("Busca tus libros y registra los préstamos directamente en la pantalla.")

if df.empty:
    st.warning("Cargando la base de datos o documento inaccesible...")
else:
    columnas_reales = df.columns.tolist()
    
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
            prestado_actual = str(row["Dejado a:"]).strip()
            
            with st.expander(f"📖 {titulo_libro} — *{autor_libro}*"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📍 **Ubicación:** {lugar} — {donde}")
                    if prestado_actual and prestado_actual != "nan" and prestado_actual != "":
                        st.error(f"🔴 Prestado a: **{prestado_actual}**")
                    else:
                        st.success("✅ Disponible en la estantería")
                with col2:
                    nuevo_input = st.text_input("Dejado a:", value=prestado_actual if (prestado_actual != "nan" and prestado_actual != "") else "", key=f"inp_{index}")
                    
                    if st.button("💾 Guardar Cambios", key=f"btn_{index}"):
                        if os.path.exists(ARCHIVO_PRESTAMOS):
                            try:
                                df_p = pd.read_csv(ARCHIVO_PRESTAMOS, index_col="Titulo")
                            except Exception:
                                df_p = pd.DataFrame(columns=["PrestadoA"])
                                df_p.index.name = "Titulo"
                        else:
                            df_p = pd.DataFrame(columns=["PrestadoA"])
                            df_p.index.name = "Titulo"
                            
                        if nuevo_input.strip() == "":
                            if titulo_libro in df_p.index:
                                df_p = df_p.drop(titulo_libro)
                        else:
                            df_p.loc[titulo_libro, "PrestadoA"] = nuevo_input.strip()
                            
                        df_p.to_csv(ARCHIVO_PRESTAMOS)
                        st.success("¡Cambio guardado!")
                        st.cache_data.clear()
                        st.rerun()
                        
        st.markdown("---")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No se encontraron libros.")
