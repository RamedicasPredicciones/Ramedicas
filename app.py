import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import math
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="RAMÉDICAS - Alternativas", layout="wide")

# Sidebar para navegación entre pestañas
with st.sidebar:
    seleccion = option_menu(
        "Menú de Opciones",
        ["Alternativas para Faltantes", "Búsqueda por Código"],
        icons=["file-earmark-plus", "search"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5px"},
            "icon": {"color": "orange"},
            "nav-link": {
                "font-size": "18px",
                "text-align": "left",
                "margin": "5px",
            },
            "nav-link-selected": {"background-color": "#FF5800"},
        },
    )

# --- Pestaña 1: Alternativas para Faltantes ---
if seleccion == "Alternativas para Faltantes":
    st.title("🛒 Alternativas para Faltantes")
    
    # Enlace de la plantilla
    PLANTILLA_URL = "https://docs.google.com/spreadsheets/d/1CPMBfCiuXq2_l8KY68HgexD-kyNVJ2Ml/export?format=xlsx"
    
    # Función para cargar inventario
    def load_inventory_file():
        inventario_url = "https://docs.google.com/spreadsheets/d/1WV4la88gTl6OUgqQ5UM0IztNBn_k4VrC/export?format=xlsx&sheet=Hoja3"
        inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja3")
        inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()
        return inventario_api_df

    # Función para procesar faltantes
    def procesar_faltantes(faltantes_df, inventario_api_df, columnas_adicionales, bodega_seleccionada):
        faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
        inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()

        if not {'codart', 'cur', 'embalaje'}.issubset(faltantes_df.columns):
            st.error("El archivo de faltantes debe contener las columnas: 'codart', 'cur' y 'embalaje'")
            return pd.DataFrame()

        faltantes_df = faltantes_df[faltantes_df['embalaje'] > 0]
        alternativas_disponibles_df = pd.merge(
            faltantes_df,
            inventario_api_df,
            on='cur',
            how='inner'
        )
        alternativas_disponibles_df = alternativas_disponibles_df[
            alternativas_disponibles_df['bodega'].isin(bodega_seleccionada)
        ]
        return alternativas_disponibles_df

    # Interfaz de usuario
    st.markdown(
        f"""
        <a href="{PLANTILLA_URL}" download>
            <button style="background-color: #FF5800; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer;">
                Descargar plantilla
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )

    # Subir archivo de faltantes
    uploaded_file = st.file_uploader("Sube el archivo de faltantes:", type=["xlsx", "csv"])
    if uploaded_file:
        faltantes_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        inventario_api_df = load_inventory_file()

        # Selección de bodegas
        bodega_seleccionada = st.multiselect(
            "Selecciona las bodegas:",
            inventario_api_df['bodega'].unique()
        )

        alternativas_disponibles_df = procesar_faltantes(faltantes_df, inventario_api_df, [], bodega_seleccionada)
        st.write("Alternativas disponibles:")
        st.dataframe(alternativas_disponibles_df)

# --- Pestaña 2: Búsqueda por Código ---
elif seleccion == "Búsqueda por Código":
    st.title("🔍 Búsqueda por Código")
    
    # Función para cargar el inventario
    def load_inventory_file():
        inventario_url = "https://docs.google.com/spreadsheets/d/19myWtMrvsor2P_XHiifPgn8YKdTWE39O/export?format=xlsx"
        inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
        inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()
        return inventario_api_df

    # Función para procesar alternativas
    def procesar_alternativas(faltantes_df, inventario_api_df):
        faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()

        if not {'cur', 'codart', 'embalaje'}.issubset(faltantes_df.columns):
            st.error("El archivo de faltantes debe contener las columnas: 'cur', 'codart' y 'embalaje'")
            return pd.DataFrame()

        cur_faltantes = faltantes_df['cur'].unique()
        alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

        columnas_necesarias = ['codart', 'cur', 'opcion', 'nomart', 'carta', 'descontinuado']
        for columna in columnas_necesarias:
            if columna not in alternativas_inventario_df.columns:
                st.error(f"La columna '{columna}' no se encuentra en el inventario. Verifica el archivo de origen.")
                st.stop()

        alternativas_inventario_df['opcion'] = alternativas_inventario_df['opcion'].fillna(0).astype(int)
        alternativas_inventario_df = alternativas_inventario_df.rename(columns={
            'codart': 'codart_alternativa'
        })
        alternativas_disponibles_df = pd.merge(
            faltantes_df,
            alternativas_inventario_df,
            on='cur',
            how='inner'
        )
        return alternativas_disponibles_df

    # Descargar plantilla
    def descargar_plantilla():
        return "https://docs.google.com/spreadsheets/d/1DWK-kyp5fy_AmjDrj9UUiiWIynT6ob3N/export?format=xlsx"

    st.markdown(
        f"""
        <a href="{descargar_plantilla()}" download>
            <button style="background-color: #FF5800; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer;">
                Descargar plantilla
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )

    # Subir archivo
    uploaded_file = st.file_uploader("Sube el archivo con los productos faltantes:", type=["xlsx", "csv"])
    if uploaded_file:
        faltantes_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        inventario_api_df = load_inventory_file()

        alternativas_disponibles_df = procesar_alternativas(faltantes_df, inventario_api_df)
        st.write("Alternativas disponibles:")
        st.dataframe(alternativas_disponibles_df)

