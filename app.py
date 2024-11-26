import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import math
from io import BytesIO

# Funciones compartidas
def load_inventory_file(url, sheet_name="Hoja1"):
    return pd.read_excel(url, sheet_name=sheet_name)

def descargar_plantilla(url):
    return url

# Configuración del diseño de Streamlit
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

# Pestaña 1: Alternativas para Faltantes
if seleccion == "Alternativas para Faltantes":
    st.title("🛒 Alternativas para Faltantes")
    PLANTILLA_URL = "https://docs.google.com/spreadsheets/d/1CPMBfCiuXq2_l8KY68HgexD-kyNVJ2Ml/export?format=xlsx"
    INVENTARIO_URL = "https://docs.google.com/spreadsheets/d/1WV4la88gTl6OUgqQ5UM0IztNBn_k4VrC/export?format=xlsx&sheet=Hoja3"

    st.markdown(
        """
        <h3 style="color: #3A86FF;">Generador de Alternativas</h3>
        <p>Sube un archivo con los productos faltantes y obtén las alternativas disponibles según el inventario actual.</p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <a href="{descargar_plantilla(PLANTILLA_URL)}" download>
            <button style="background-color: #FF5800; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer;">
                📥 Descargar plantilla de faltantes
            </button>
        </a>
        """,
        unsafe_allow_html=True,
    )

    # Subir archivo
    uploaded_file = st.file_uploader("📤 Subir tu archivo de faltantes (xlsx)", type="xlsx")

    if uploaded_file:
        faltantes_df = pd.read_excel(uploaded_file)
        inventario_df = load_inventory_file(INVENTARIO_URL, sheet_name="Hoja3")
        faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()
        inventario_df.columns = inventario_df.columns.str.lower().str.strip()

        # Procesar faltantes
        columnas_necesarias = {'cur', 'codart', 'faltante', 'embalaje'}
        if not columnas_necesarias.issubset(faltantes_df.columns):
            st.error(f"❌ El archivo de faltantes debe contener las columnas: {', '.join(columnas_necesarias)}")
            st.stop()

        cur_faltantes = faltantes_df['cur'].unique()
        alternativas_inventario_df = inventario_df[inventario_df['cur'].isin(cur_faltantes)]

        alternativas_inventario_df = alternativas_inventario_df[alternativas_inventario_df['unidadespresentacionlote'] > 0]

        alternativas_inventario_df.rename(columns={
            'codart': 'codart_alternativa',
            'opcion': 'opcion_alternativa',
            'embalaje': 'embalaje_alternativa',
            'unidadespresentacionlote': 'Existencias codart alternativa'
        }, inplace=True)

        alternativas_disponibles_df = pd.merge(
            faltantes_df[['cur', 'codart', 'faltante', 'embalaje']],
            alternativas_inventario_df,
            on='cur',
            how='inner'
        )

        # Filtrar registros donde opcion_alternativa sea mayor a 0
        alternativas_disponibles_df = alternativas_disponibles_df[alternativas_disponibles_df['opcion_alternativa'] > 0]

        # Agregar columna de cantidad necesaria ajustada por embalaje
        alternativas_disponibles_df['cantidad_necesaria'] = alternativas_disponibles_df.apply(
            lambda row: math.ceil(row['faltante'] * row['embalaje'] / row['embalaje_alternativa'])
            if pd.notnull(row['embalaje']) and pd.notnull(row['embalaje_alternativa']) and row['embalaje_alternativa'] > 0
            else None,
            axis=1
        )

        alternativas_disponibles_df.sort_values(by=['codart', 'Existencias codart alternativa'], inplace=True)

        mejores_alternativas = []
        for codart_faltante, group in alternativas_disponibles_df.groupby('codart'):
            faltante_cantidad = group['faltante'].iloc[0]

            # Buscar en la bodega seleccionada
            mejor_opcion_bodega = group[group['Existencias codart alternativa'] >= faltante_cantidad]
            mejor_opcion = mejor_opcion_bodega.head(1) if not mejor_opcion_bodega.empty else group.nlargest(1, 'Existencias codart alternativa')

            mejores_alternativas.append(mejor_opcion.iloc[0])

        resultado_final_df = pd.DataFrame(mejores_alternativas)

        # Nuevas columnas para verificar si el faltante fue suplido y el faltante restante
        resultado_final_df['suplido'] = resultado_final_df.apply(
            lambda row: 'SI' if row['Existencias codart alternativa'] >= row['cantidad_necesaria'] else 'NO',
            axis=1
        )

        resultado_final_df['faltante_restante alternativa'] = resultado_final_df.apply(
            lambda row: row['cantidad_necesaria'] - row['Existencias codart alternativa'] if row['suplido'] == 'NO' else 0,
            axis=1
        )

        st.success("✔️ Procesamiento completado.")
        st.dataframe(resultado_final_df)

        # Exportar archivo
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Alternativas')
            output.seek(0)
            return output

        st.download_button(
            label="📥 Descargar archivo de alternativas",
            data=to_excel(resultado_final_df),
            file_name="alternativas_faltantes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# Pestaña 2: Búsqueda por Código
elif seleccion == "Búsqueda por Código":
    st.title("🔍 Búsqueda por Código")
# Función para cargar el inventario desde Google Sheets
def load_inventory_file():
    inventario_url = "https://docs.google.com/spreadsheets/d/19myWtMrvsor2P_XHiifPgn8YKdTWE39O/export?format=xlsx"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()  # Asegurar nombres consistentes
    return inventario_api_df

# Función para procesar las alternativas basadas en los productos faltantes
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

    # Se agrega la columna 'descontinuado' al DataFrame de alternativas
    alternativas_inventario_df = alternativas_inventario_df[['cur', 'codart_alternativa', 'opcion', 'nomart', 'carta', 'descontinuado']]

    alternativas_disponibles_df = pd.merge(
        faltantes_df,
        alternativas_inventario_df,
        on='cur',
        how='inner'
    )

    return alternativas_disponibles_df

# Función para generar un archivo Excel
def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alternativas')
    output.seek(0)
    return output

# Función para descargar la plantilla
def descargar_plantilla():
    plantilla_url = "https://docs.google.com/spreadsheets/d/1DWK-kyp5fy_AmjDrj9UUiiWIynT6ob3N/export?format=xlsx"
    return plantilla_url

# Interfaz de Streamlit
st.markdown(
    """
    <h1 style="text-align: center; color: #FF5800; font-family: Arial, sans-serif;">
        RAMEDICAS S.A.S.
    </h1>
    <h3 style="text-align: center; font-family: Arial, sans-serif; color: #3A86FF;">
        Buscador de Alternativas por Código de Artículo
    </h3>
    <p style="text-align: center; font-family: Arial, sans-serif; color: #6B6B6B;">
        Esta herramienta te permite buscar y consultar los códigos alternativos de productos con las opciones deseadas de manera eficiente y rápida.
    </p>
    """,
    unsafe_allow_html=True
)

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

# Subir archivo de faltantes
uploaded_file = st.file_uploader("Sube un archivo con los productos faltantes (contiene 'codart', 'cur' y 'embalaje')", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('xlsx'):
        faltantes_df = pd.read_excel(uploaded_file)
    else:
        faltantes_df = pd.read_csv(uploaded_file)

    inventario_api_df = load_inventory_file()

    alternativas_disponibles_df = procesar_alternativas(faltantes_df, inventario_api_df)

    if not alternativas_disponibles_df.empty:
        st.write("Filtra las alternativas por opciones:")

        # Filtrar las opciones disponibles para excluir el valor 0
        opciones_disponibles = alternativas_disponibles_df['opcion'].unique().tolist()
        opciones_disponibles = [opcion for opcion in opciones_disponibles if opcion != 0]  # Eliminar opción 0

        opciones_seleccionadas = st.multiselect(
            "Selecciona las opciones que deseas visualizar:",
            options=opciones_disponibles,
            default=[]  # Sin opciones seleccionadas por defecto
        )

        # Filtrar el dataframe según las opciones seleccionadas
        alternativas_filtradas_df = alternativas_disponibles_df[
            alternativas_disponibles_df['opcion'].isin(opciones_seleccionadas)
        ]

        st.write("Alternativas disponibles filtradas:")
        st.dataframe(alternativas_filtradas_df[['codart', 'cur', 'codart_alternativa', 'opcion', 'nomart', 'carta', 'descontinuado']])

        if not alternativas_filtradas_df.empty:
            excel_file = generar_excel(alternativas_filtradas_df[['codart', 'cur', 'codart_alternativa', 'opcion', 'nomart', 'carta', 'descontinuado']])
            st.download_button(
                label="Descargar archivo Excel con las alternativas filtradas",
                data=excel_file,
                file_name="alternativas_filtradas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No hay alternativas disponibles para las opciones seleccionadas.")
    else:
        st.write("No se encontraron alternativas para los códigos ingresados.")
