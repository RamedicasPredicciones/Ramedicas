import streamlit as st
import pandas as pd
import math
from io import BytesIO

# Cargar y procesar la información del primer código (Alternativas por Código de Artículo)
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/19myWtMrvsor2P_XHiifPgn8YKdTWE39O/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()  # Asegurar nombres consistentes
    return inventario_api_df

def procesar_alternativas(faltantes_df, inventario_api_df):
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
    if not {'cur', 'codart', 'embalaje'}.issubset(faltantes_df.columns):
        st.error("El archivo de faltantes debe contener las columnas: 'cur', 'codart' y 'embalaje'")
        return pd.DataFrame()

    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    alternativas_inventario_df['opcion'] = alternativas_inventario_df['opcion'].fillna(0).astype(int)
    alternativas_inventario_df = alternativas_inventario_df.rename(columns={'codart': 'codart_alternativa'})
    alternativas_inventario_df = alternativas_inventario_df[['cur', 'codart_alternativa', 'opcion', 'nomart', 'carta', 'descontinuado']]

    alternativas_disponibles_df = pd.merge(faltantes_df, alternativas_inventario_df, on='cur', how='inner')

    return alternativas_disponibles_df

# Cargar y procesar la información del segundo código (Generador de Alternativas para Faltantes)
PLANTILLA_URL = "https://docs.google.com/spreadsheets/d/1CPMBfCiuXq2_l8KY68HgexD-kyNVJ2Ml/export?format=xlsx"
def load_inventory_file_bodega():
    inventario_url = "https://docs.google.com/spreadsheets/d/1WV4la88gTl6OUgqQ5UM0IztNBn_k4VrC/export?format=xlsx&sheet=Hoja3"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja3")
    return inventario_api_df

def procesar_faltantes(faltantes_df, inventario_api_df, columnas_adicionales, bodega_seleccionada):
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()

    columnas_necesarias = {'cur', 'codart', 'faltante', 'embalaje'}
    if not columnas_necesarias.issubset(faltantes_df.columns):
        st.error(f"El archivo de faltantes debe contener las columnas: {', '.join(columnas_necesarias)}")
        return pd.DataFrame()

    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    if bodega_seleccionada:
        alternativas_inventario_df = alternativas_inventario_df[alternativas_inventario_df['bodega'].isin(bodega_seleccionada)]

    alternativas_disponibles_df = alternativas_inventario_df[alternativas_inventario_df['unidadespresentacionlote'] > 0]

    alternativas_disponibles_df.rename(columns={
        'codart': 'codart_alternativa',
        'opcion': 'opcion_alternativa',
        'embalaje': 'embalaje_alternativa',
        'unidadespresentacionlote': 'Existencias codart alternativa'
    }, inplace=True)

    alternativas_disponibles_df = pd.merge(faltantes_df[['cur', 'codart', 'faltante', 'embalaje']],
                                            alternativas_disponibles_df,
                                            on='cur', how='inner')

    alternativas_disponibles_df = alternativas_disponibles_df[alternativas_disponibles_df['opcion_alternativa'] > 0]

    alternativas_disponibles_df['cantidad_necesaria'] = alternativas_disponibles_df.apply(
        lambda row: math.ceil(row['faltante'] * row['embalaje'] / row['embalaje_alternativa'])
        if pd.notnull(row['embalaje']) and pd.notnull(row['embalaje_alternativa']) and row['embalaje_alternativa'] > 0
        else None, axis=1
    )

    alternativas_disponibles_df.sort_values(by=['codart', 'Existencias codart alternativa'], inplace=True)
    return alternativas_disponibles_df

# Interfaz con pestañas
st.markdown("""
    <h1 style="text-align: center; color: #FF5800;">RAMEDICAS S.A.S.</h1>
""", unsafe_allow_html=True)

# Selección de pestaña
tab = st.radio("Selecciona una opción:", ["Alternativas por Código de Artículo", "Generador de Alternativas para Faltantes"])

if tab == "Alternativas por Código de Artículo":
    # Función del primer código
    st.subheader("Buscar Alternativas por Código de Artículo")
    
    uploaded_file = st.file_uploader("Sube un archivo con los productos faltantes (contiene 'codart', 'cur' y 'embalaje')", type=["xlsx", "csv"])

    if uploaded_file:
        if uploaded_file.name.endswith('xlsx'):
            faltantes_df = pd.read_excel(uploaded_file)
        else:
            faltantes_df = pd.read_csv(uploaded_file)

        inventario_api_df = load_inventory_file()
        alternativas_disponibles_df = procesar_alternativas(faltantes_df, inventario_api_df)

        if not alternativas_disponibles_df.empty:
            st.write("Alternativas disponibles:")
            st.dataframe(alternativas_disponibles_df[['codart', 'cur', 'codart_alternativa', 'opcion', 'nomart', 'carta', 'descontinuado']])
        else:
            st.write("No se encontraron alternativas.")

if tab == "Generador de Alternativas para Faltantes":
    # Función del segundo código
    st.subheader("Generar Alternativas para Faltantes")

    uploaded_file = st.file_uploader("Sube tu archivo de faltantes", type="xlsx")
    
    if uploaded_file:
        faltantes_df = pd.read_excel(uploaded_file)
        inventario_api_df = load_inventory_file_bodega()

        bodegas_disponibles = inventario_api_df['bodega'].unique().tolist()
        bodega_seleccionada = st.multiselect("Seleccione la bodega", options=bodegas_disponibles, default=[])

        columnas_adicionales = st.multiselect(
            "Selecciona columnas adicionales para incluir en el archivo final:",
            options=["presentacionart", "numlote", "fechavencelote"],
            default=[]
        )

        resultado_final_df = procesar_faltantes(faltantes_df, inventario_api_df, columnas_adicionales, bodega_seleccionada)
        
        if not resultado_final_df.empty:
            st.write("Resultado Final:")
            st.dataframe(resultado_final_df[['cur', 'codart', 'faltante', 'embalaje', 'codart_alternativa', 'opcion_alternativa', 'embalaje_alternativa', 'cantidad_necesaria', 'Existencias codart alternativa', 'bodega', 'suplido']])
        else:
            st.write("No se generaron alternativas.")
