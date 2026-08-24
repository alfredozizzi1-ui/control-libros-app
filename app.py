import streamlit as st
from pyairtable import Api
from streamlit_drawable_canvas import st_canvas
import time

# Configuración de página adaptada a móviles
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

# Credenciales desde Secrets
AIRTABLE_TOKEN = st.secrets.get("AIRTABLE_TOKEN", "")
BASE_ID = st.secrets.get("BASE_ID", "")
TABLE_NAME = "Seguimiento producción"

# Lectura de datos con caché persistente (ttl=600 segundos / 10 minutos)
@st.cache_data(ttl=600, show_spinner=False)
def cargar_datos():
    api = Api(AIRTABLE_TOKEN)
    table = api.table(BASE_ID, TABLE_NAME)
    records = table.all()
    datos = []
    for r in records:
        row = r['fields']
        row['id'] = r['id']
        datos.append(row)
    return datos

st.title("📱 Producción de Libros")

# Botón para refrescar datos manualmente
if st.button("🔄 Actualizar datos de Airtable"):
    st.cache_data.clear()
    st.rerun()

try:
    datos = cargar_datos()
    api = Api(AIRTABLE_TOKEN)
    table = api.table(BASE_ID, TABLE_NAME)

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("🔍 Filtros")
    
    editoriales = list(set([d.get("Editorial", "Sin asignación") for d in datos if "Editorial" in d]))
    ed_seleccionada = st.sidebar.multiselect("Editorial:", editoriales, default=editoriales)
    
    estados_autor = list(set([d.get("Revisión Autor", "Sin estado") for d in datos if "Revisión Autor" in d]))
    estado_autor_sel = st.sidebar.multiselect("Revisión Autor:", estados_autor, default=estados_autor)

    # Filtrar datos
    datos_filtrados = [
        d for d in datos 
        if d.get("Editorial") in ed_seleccionada 
        and d.get("Revisión Autor", "Sin estado") in estado_autor_sel
    ]

    # --- MÉTRICAS VISTA MÓVIL ---
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
            
            st.markdown("---")
            st.write(f"📝 **Rev. Editorial:** {libro.get('Revisión Editorial', 'N/A')}")
            st.write(f"📐 **Maquetación:** {libro.get('Maquetación', 'N/A')}")
            st.write(f"🎨 **Portada:** {libro.get('Portada', 'N/A')}")
            st.write(f"✍️ **Rev. Autor:** {rev_autor}")
            st.write(f"⚖️ **Depósito Legal:** {'✅' if libro.get('Depósito Legal') else '⏳'}")

            st.markdown("---")
            st.markdown("#### ✍️ Firma de Conformidad")
            
            if rev_autor == "Aprobado":
                st.success("✅ Este libro ya fue firmado y aprobado.")
            else:
                st.caption("Firma con el dedo dentro del recuadro:")
                
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0)",
                    stroke_width=3,
                    stroke_color="#000000",
                    background_color="#FFFFFF",
                    height=160,
                    width=280,
                    drawing_mode="freedraw",
                    key=f"canvas_{libro['id']}",
                )

                if st.button("Guardar Firma y Aprobar", key=f"btn_{libro['id']}"):
                    if canvas_result.image_data is not None:
                        table.update(libro['id'], {
                            "Revisión Autor": "Aprobado"
                        })
                        st.cache_data.clear()
                        st.success(f"¡'{titulo}' actualizado como Aprobado!")
                        time.sleep(1)
                        st.rerun()

except Exception as e:
    st.warning("⏳ Airtable está pausando las peticiones por exceso de tráfico. Aguarda unos 30 segundos y pulsa 'Actualizar datos de Airtable'.")
