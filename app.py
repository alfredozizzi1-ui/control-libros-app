import streamlit as st
from pyairtable import Api
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# Configuración de página adaptada a móviles (inicia con la barra lateral replegada)
st.set_page_config(
    page_title="Producción Libros", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS para optimizar la interfaz en teléfonos móviles
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3rem;
        font-weight: bold;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Conexión a Airtable desde Secrets
AIRTABLE_TOKEN = st.secrets.get("AIRTABLE_TOKEN", "")
BASE_ID = st.secrets.get("BASE_ID", "")
TABLE_NAME = "Seguimiento producción"

# Lectura de datos con caché de 5 minutos para evitar bloqueos por límite de peticiones (Rate Limit 429)
@st.cache_data(ttl=300)
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

st.title("📱 Producción de Libros")

# Botón destacado para refrescar los datos manualmente en el móvil
if st.button("🔄 Actualizar datos de Airtable"):
    st.cache_data.clear()
    st.rerun()

try:
    datos, table = cargar_datos()

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por Editorial
    editoriales = list(set([d.get("Editorial", "Sin asignación") for d in datos if "Editorial" in d]))
    ed_seleccionada = st.sidebar.multiselect("Editorial:", editoriales, default=editoriales)
    
    # Filtro por Revisión Autor
    estados_autor = list(set([d.get("Revisión Autor", "Sin estado") for d in datos if "Revisión Autor" in d]))
    estado_autor_sel = st.sidebar.multiselect("Revisión Autor:", estados_autor, default=estados_autor)

    # Filtrar registros
    datos_filtrados = [
        d for d in datos 
        if d.get("Editorial") in ed_seleccionada 
        and d.get("Revisión Autor", "Sin estado") in estado_autor_sel
    ]

    # --- MÉTRICAS (Estructura en vertical para pantallas pequeñas) ---
    st.metric("Total Libros", len(datos_filtrados))
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Pendientes Autor", len([d for d in datos_filtrados if d.get("Revisión Autor") == "Pendiente"]))
    with col_m2:
        st.metric("Aprobados", len([d for d in datos_filtrados if d.get("Revisión Autor") == "Aprobado"]))

    st.divider()

    # --- LISTA DE LIBROS Y MÓDULO DE FIRMA ---
    st.subheader("📚 Libros en Edición")

    for libro in datos_filtrados:
        titulo = libro.get('Titulo Libro', 'Sin Título')
        editorial = libro.get('Editorial', 'Sin Editorial')
        rev_autor = libro.get('Revisión Autor', 'Pendiente')
        
        with st.expander(f"📖 {titulo} ({editorial})"):
            st.markdown(f"**Estado Global:** {libro.get('Estado global', 'En curso')}")
            st.write(f"💰 **Presupuesto:** {libro.get('Presupuesto', 'N/A')} | **50% Pago:** {'✅' if libro.get('50% €') else '❌'}")
            
            # Fases del proyecto
            st.markdown("---")
            st.write(f"📝 **Rev. Editorial:** {libro.get('Revisión Editorial', 'N/A')}")
            st.write(f"📐 **Maquetación:** {libro.get('Maquetación', 'N/A')}")
            st.write(f"🎨 **Portada:** {libro.get('Portada', 'N/A')}")
            st.write(f"✍️ **Rev. Autor:** {rev_autor}")
            st.write(f"⚖️ **Depósito Legal:** {'✅' if libro.get('Depósito Legal') else '⏳'}")

            # Módulo táctil para la firma en móvil
            st.markdown("---")
            st.markdown("#### ✍️ Firma de Conformidad")
            
            if rev_autor == "Aprobado":
                st.success("✅ Este libro ya fue firmado y aprobado.")
            else:
                st.caption("Firma con el dedo o stylus dentro del recuadro:")
                
                # Lienzo adaptado a la anchura media de un smartphone (300px)
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0)",
                    stroke_width=3,
                    stroke_color="#000000",
                    background_color="#FFFFFF",
                    height=160,
                    width=300,
                    drawing_mode="freedraw",
                    key=f"canvas_{libro['id']}",
                )

                if st.button("Guardar Firma y Aprobar", key=f"btn_{libro['id']}"):
                    if canvas_result.image_data is not None:
                        # Actualiza el registro en Airtable a Aprobado
                        table.update(libro['id'], {
                            "Revisión Autor": "Aprobado"
                        })
                        st.cache_data.clear()
                        st.success(f"¡'{titulo}' guardado como Aprobado!")
                        st.rerun()

except Exception as e:
    st.error(f"Error de conexión con Airtable: {e}")
