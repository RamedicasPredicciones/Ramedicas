import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Faltantes y Alternativas",
    page_icon="📦",
    layout="wide"
)

# -----------------------------------
# CÓDIGO 1: Alternativas filtradas por opciones
# -----------------------------------
def codigo_1():
    st.header("Gestión de Alternativas por Opciones")
    
    # Subir archivo de faltantes
    faltantes_file = st.file_uploader("Sube tu archivo de faltantes (faltantes.xlsx)", type=['xlsx'])
    if faltantes_file:
        faltantes = pd.read_excel(faltantes_file)
        st.write("Vista previa de faltantes cargados:", faltantes.head())

        # Subir archivo de inventario
        inventario_file = st.file_uploader("Sube tu archivo de inventario (inventario.xlsx)", type=['xlsx'])
        if inventario_file:
            inventario = pd.read_excel(inventario_file)
            st.write("Vista previa del inventario cargado:", inventario.head())

            # Filtrar por opciones
            opciones = st.multiselect(
                "Selecciona las opciones de alternativas (columna 'opcion')",
                options=inventario['opcion'].unique()
            )
            if opciones:
                alternativas = inventario[inventario['opcion'].isin(opciones)]
                st.write("Alternativas seleccionadas:", alternativas.head())

                # Descargar archivo filtrado
                st.download_button(
                    label="Descargar alternativas filtradas",
                    data=alternativas.to_excel(index=False),
                    file_name="alternativas_filtradas.xlsx"
                )

# -----------------------------------
# CÓDIGO 2: Gestión avanzada de faltantes
# -----------------------------------
def codigo_2():
    st.header("Gestión Avanzada de Faltantes por Bodega y Embalaje")

    # Subir archivo de faltantes
    faltantes_file = st.file_uploader("Sube tu archivo de faltantes (faltantes_2.xlsx)", type=['xlsx'], key="faltantes_2")
    if faltantes_file:
        faltantes = pd.read_excel(faltantes_file)
        st.write("Vista previa de faltantes cargados:", faltantes.head())

        # Subir archivo de inventario
        inventario_file = st.file_uploader("Sube tu archivo de inventario (inventario_2.xlsx)", type=['xlsx'], key="inventario_2")
        if inventario_file:
            inventario = pd.read_excel(inventario_file)
            st.write("Vista previa del inventario cargado:", inventario.head())

            # Filtrar por bodega
            bodegas = st.multiselect(
                "Selecciona la bodega (columna 'bodega')",
                options=inventario['bodega'].unique()
            )
            if bodegas:
                inventario_filtrado = inventario[inventario['bodega'].isin(bodegas)]

                # Lógica para calcular faltantes ajustados
                faltantes['cantidad_necesaria'] = faltantes['faltante'] * faltantes['embalaje']
                inventario_filtrado['suplido'] = inventario_filtrado['cantidad'] - faltantes['cantidad_necesaria']
                faltantes['faltante_restante'] = faltantes['cantidad_necesaria'] - inventario_filtrado['cantidad']

                st.write("Resultados después del cálculo:", faltantes.head())

                # Descargar archivo procesado
                st.download_button(
                    label="Descargar resultados procesados",
                    data=faltantes.to_excel(index=False),
                    file_name="resultados_faltantes.xlsx"
                )

# -----------------------------------
# Selección de sección
# -----------------------------------
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Selecciona el módulo", ["Alternativas por Opciones", "Gestión Avanzada de Faltantes"])

if opcion == "Alternativas por Opciones":
    codigo_1()
elif opcion == "Gestión Avanzada de Faltantes":
    codigo_2()
