import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Faltantes",
    page_icon="📦",
    layout="wide"
)

# Funciones auxiliares
def descargar_excel(df, nombre_archivo):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output, nombre_archivo

# Plantillas de ejemplo
faltantes_template = pd.DataFrame({"cur": [], "embalaje": [], "codart": []})
opciones_template = pd.DataFrame({
    "cur": [],
    "nombre": [],
    "laboratorio": [],
    "presentación": [],
    "cantidad": []
})
inventario_template = pd.DataFrame({
    "codart": [], "cur": [], "cantidad": [], "bodega": [], "embalaje": []
})

# Sidebar
with st.sidebar:
    st.image("https://i.imgur.com/ZiA6Kc3.png", use_column_width=True)
    st.title("📦 Gestión de Faltantes")
    opcion = st.radio(
        "Selecciona una tarea:",
        ["Inicio", "Cargar Faltantes", "Cargar Inventario", "Procesar Alternativas"]
    )
    st.write("---")
    st.info("Selecciona una tarea en el menú para comenzar.")

# Contenido principal
if opcion == "Inicio":
    st.title("📦 Gestión de Faltantes - Inicio")
    st.write("""
    Bienvenido a la aplicación de gestión de faltantes. 
    Usa el menú lateral para navegar entre las opciones.
    """)
    st.markdown("### Funciones principales:")
    st.write("- **Cargar Faltantes:** Subir un archivo con los productos faltantes.")
    st.write("- **Cargar Inventario:** Subir un archivo con el inventario disponible.")
    st.write("- **Procesar Alternativas:** Generar un archivo con sugerencias de productos alternativos.")

elif opcion == "Cargar Faltantes":
    st.title("📥 Cargar Faltantes")
    st.write("Sube un archivo con los faltantes. Asegúrate de que tenga las columnas correctas.")
    
    uploaded_file = st.file_uploader("Sube tu archivo de faltantes", type=["xlsx"])
    
    if uploaded_file:
        faltantes_df = pd.read_excel(uploaded_file)
        st.success("Archivo cargado exitosamente.")
        st.dataframe(faltantes_df)
    else:
        st.warning("No se ha subido ningún archivo.")

    # Botón para descargar plantilla
    output, nombre_archivo = descargar_excel(faltantes_template, "plantilla_faltantes.xlsx")
    st.download_button(
        label="Descargar plantilla de faltantes",
        data=output,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif opcion == "Cargar Inventario":
    st.title("📥 Cargar Inventario")
    st.write("Sube un archivo con el inventario disponible.")
    
    uploaded_file = st.file_uploader("Sube tu archivo de inventario", type=["xlsx"])
    
    if uploaded_file:
        inventario_df = pd.read_excel(uploaded_file)
        st.success("Archivo cargado exitosamente.")
        st.dataframe(inventario_df)
    else:
        st.warning("No se ha subido ningún archivo.")

    # Botón para descargar plantilla
    output, nombre_archivo = descargar_excel(inventario_template, "plantilla_inventario.xlsx")
    st.download_button(
        label="Descargar plantilla de inventario",
        data=output,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif opcion == "Procesar Alternativas":
    st.title("⚙️ Procesar Alternativas")
    st.write("Sube los archivos necesarios para generar las alternativas.")

    # Subir faltantes
    faltantes_file = st.file_uploader("Sube tu archivo de faltantes", type=["xlsx"])
    
    # Subir inventario
    inventario_file = st.file_uploader("Sube tu archivo de inventario", type=["xlsx"])
    
    if faltantes_file and inventario_file:
        faltantes_df = pd.read_excel(faltantes_file)
        inventario_df = pd.read_excel(inventario_file)

        # Filtrar inventario disponible
        inventario_df = inventario_df[inventario_df["cantidad"] > 0]

        # Generar alternativas
        alternativas = faltantes_df.merge(inventario_df, on="cur", how="left")
        alternativas = alternativas[[
            "cur", "codart_x", "embalaje_x", "codart_y", "cantidad", "bodega", "embalaje_y"
        ]].rename(columns={
            "codart_x": "codart_faltante",
            "embalaje_x": "embalaje",
            "codart_y": "codart_alternativa",
            "embalaje_y": "embalaje_alternativa"
        })

        st.success("Alternativas procesadas exitosamente.")
        st.dataframe(alternativas)

        # Botón para descargar archivo procesado
        output, nombre_archivo = descargar_excel(alternativas, "alternativas.xlsx")
        st.download_button(
            label="Descargar alternativas procesadas",
            data=output,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Sube los archivos de faltantes e inventario para continuar.")

# Footer
st.markdown("---")
st.markdown("Creado con ❤️ por Laura")
