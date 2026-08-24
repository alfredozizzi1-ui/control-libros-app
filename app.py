import streamlit as st
from pyairtable import Api
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# Configuración inicial de la página
st.set_page_config(page_title="Producción Libros Algani + Ibhuku", layout="wide")

# Conexión con Airtable
AIRTABLE_TOKEN = st.secrets.get("AIRTABLE_TOKEN", "TU_TOKEN_AQUI")
BASE_ID = st.secrets.get("BASE_ID", "TU_BASE_ID_AQUI")
TABLE_NAME = "Seguimiento producción"

@st.cache_data(ttl=30)
def cargar_datos():
    api = Api(AIRTABLE_TOKEN)
    table = api.table(BASE_ID, TABLE_NAME)
    records = table.all()
    datos = []
    for r in records:
        row = r['fields']
        row['id'] = r['id']
        datos.append(row)
    return datos, table

st.title("📚 Panel de Seguimiento de Producción")

try:
    datos, table = cargar_datos()

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    # Filtro por Editorial
    editoriales = list(set([d.get("Editorial", "Sin asignación") for d in datos if "Editorial" in d]))
    ed_seleccionada = st.sidebar.multiselect("Editorial:", editoriales, default=editoriales)
    
    # Filtro por Estado Autor
    estados_autor = list(set([d.get("Revisión Autor", "Sin estado") for d in datos if "Revisión Autor" in d]))
    estado_autor_sel = st.sidebar.multiselect("Estado Revisión Autor:", estados_autor, default=estados_autor)

    # Filtrado de la lista
    datos_filtrados = [
        d for d in datos 
        if d.get("Editorial") in ed_seleccionada 
        and d.get("Revisión Autor", "Sin estado") in estado_autor_sel
    ]

    # --- MÉTRICAS DE CABECERA ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Proyectos", len(datos_filtrados))
    c2.metric("En Producción", len([d for d in datos_filtrados if d.get("Estado global") == "En producción"]))
    c3.metric("Pendientes Revisión Autor", len([d for d in datos_filtrados if d.get("Revisión Autor") == "Pendiente"]))
    c4.metric("Aprobados / Conforme", len([d for d in datos_filtrados if d.get("Revisión Autor") == "Aprobado"]))

    st.divider()

    # --- MÓDULO PRINCIPAL DE GESTIÓN Y FIRMA ---
    st.subheader("📋 Lista de Libros en Edición")

    for libro in datos_filtrados:
        titulo = libro.get('Titulo Libro', 'Sin Título')
        editorial = libro.get('Editorial', 'Sin Editorial')
        rev_autor = libro.get('Revisión Autor', 'Pendiente')
        
        with st.expander(f"📖 {titulo} — [{editorial}] | Revisión Autor: {rev_autor}"):
            col_info, col_firma = st.columns([1, 1])

            # Columna 1: Estado detallado de las fases
            with col_info:
                st.markdown("#### ⚙️ Estado de la Producción")
                st.write(f"**Presupuesto:** {libro.get('Presupuesto', 'N/A')} | **50% Pago:** {'✅ Sí' if libro.get('50% €') else '❌ No'}")
                st.write(f"**Revisión Editorial:** {libro.get('Revisión Editorial', 'N/A')}")
                st.write(f"**Maquetación:** {libro.get('Maquetación', 'N/A')}")
                st.write(f"**Portada:** {libro.get('Portada', 'N/A')}")
                st.write(f"**Revisión Autor:** {libro.get('Revisión Autor', 'N/A')}")
                st.write(f"**Depósito Legal:** {'✅' if libro.get('Depósito Legal') else '⏳ Pendiente'}")

            # Columna 2: Módulo de firma / Conformidad del Autor
            with col_firma:
                st.markdown("#### ✍️ Firma de Conformidad del Autor")
                
                if rev_autor == "Aprobado":
                    st.success("✅ Este libro ya ha sido aprobado y firmado por el autor.")
                else:
                    st.caption("Dibuja tu firma en la casilla inferior para aprobar la revisión:")
                    
                    canvas_result = st_canvas(
                        fill_color="rgba(255, 255, 255, 0)",
                        stroke_width=2,
                        stroke_color="#000000",
                        background_color="#F0F2F6",
                        height=150,
                        width=350,
                        drawing_mode="freedraw",
                        key=f"canvas_{libro['id']}",
                    )

                    if st.button(f"Aprobar y Registrar Firma", key=f"btn_{libro['id']}"):
                        if canvas_result.image_data is not None:
                            # 1. Actualización inmediata en Airtable
                            table.update(libro['id'], {
                                "Revisión Autor": "Aprobado"
                            })
                            st.success(f"¡Revisión de '{titulo}' aprobada correctamente!")
                            st.rerun()

except Exception as e:
    st.error(f"Error al conectar con la base de Airtable: {e}")
