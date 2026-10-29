import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# Configuración de la página
st.set_page_config(
    page_title="Radar de Señales",
    page_icon="📡",
    layout="centered"
)

# ============================================================
# ESTILOS (TEMÁTICA: RADAR DE SEÑALES)
# ============================================================

st.markdown("""
<style>

    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@500;700&display=swap');

    :root {
        --fondo: #04121F;
        --fondo-claro: #0A2236;
        --verde: #39FF88;
        --verde-oscuro: #14803F;
        --cian: #4DD8FF;
        --ambar: #FFB84D;
        --texto: #CFEFE0;
    }

    /* Fondo: pantalla de radar */
    .stApp {
        background:
            radial-gradient(circle at 50% 30%, rgba(57, 255, 136, 0.10) 0%, transparent 55%),
            repeating-linear-gradient(0deg, rgba(57, 255, 136, 0.03) 0px, rgba(57, 255, 136, 0.03) 1px, transparent 1px, transparent 40px),
            repeating-linear-gradient(90deg, rgba(57, 255, 136, 0.03) 0px, rgba(57, 255, 136, 0.03) 1px, transparent 1px, transparent 40px),
            var(--fondo);
        font-family: 'Share Tech Mono', monospace;
    }

    /* Texto general */
    .stMarkdown p, .stMarkdown li, label, .stCaption, span {
        color: var(--texto);
        font-family: 'Share Tech Mono', monospace;
    }

    /* Título */
    h1 {
        font-family: 'Orbitron', sans-serif !important;
        color: var(--verde) !important;
        text-align: center;
        font-size: 38px !important;
        letter-spacing: 3px;
        text-shadow: 0 0 10px var(--verde), 0 0 24px rgba(57, 255, 136, 0.5);
    }

    h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: var(--cian) !important;
        letter-spacing: 1px;
    }

    /* Barra lateral: panel de control */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #071A2B 0%, #04121F 100%);
        border-right: 2px solid var(--verde-oscuro);
        box-shadow: 4px 0 18px rgba(57, 255, 136, 0.15);
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--verde) !important;
    }

    /* Campos de texto y números */
    .stTextInput input,
    .stNumberInput input {
        background-color: var(--fondo-claro) !important;
        border: 1px solid var(--verde-oscuro) !important;
        border-radius: 6px !important;
        color: var(--verde) !important;
        font-family: 'Share Tech Mono', monospace !important;
    }

    .stTextInput input:focus,
    .stNumberInput input:focus {
        border-color: var(--verde) !important;
        box-shadow: 0 0 10px rgba(57, 255, 136, 0.5) !important;
    }

    /* Botón: escaneo */
    .stButton > button {
        background: transparent;
        color: var(--verde);
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        letter-spacing: 1px;
        border: 2px solid var(--verde);
        border-radius: 8px;
        padding: 12px 24px;
        box-shadow: 0 0 14px rgba(57, 255, 136, 0.4), inset 0 0 14px rgba(57, 255, 136, 0.1);
        transition: 0.2s;
    }

    .stButton > button:hover {
        background: var(--verde);
        color: var(--fondo);
        box-shadow: 0 0 26px var(--verde);
    }

    /* Tarjetas de métricas: lecturas del sensor */
    [data-testid="stMetric"] {
        background: var(--fondo-claro);
        border: 1px solid var(--verde-oscuro);
        border-left: 5px solid var(--verde);
        border-radius: 8px;
        padding: 14px;
        box-shadow: 0 0 14px rgba(57, 255, 136, 0.2);
    }

    [data-testid="stMetricLabel"] p {
        color: var(--cian) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    [data-testid="stMetricValue"] {
        color: var(--verde) !important;
        font-family: 'Orbitron', sans-serif !important;
        text-shadow: 0 0 10px rgba(57, 255, 136, 0.7);
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background: var(--fondo-claro);
        border: 1px solid var(--verde-oscuro);
        border-radius: 10px;
    }

    /* Alertas */
    [data-testid="stAlert"] {
        background: var(--fondo-claro);
        border: 1px solid var(--verde-oscuro);
        border-radius: 10px;
    }

    /* Código y JSON */
    [data-testid="stCode"], [data-testid="stJson"] {
        border: 1px solid var(--verde-oscuro);
        border-radius: 8px;
    }

    hr { border-color: var(--verde-oscuro) !important; opacity: 0.7; }

    /* Decoración */
    .subtitulo {
        text-align: center;
        color: var(--ambar);
        font-size: 16px;
        letter-spacing: 3px;
        margin-bottom: 4px;
    }

    .onda {
        text-align: center;
        color: var(--verde);
        font-size: 20px;
        letter-spacing: 10px;
        margin: 6px 0 20px 0;
        text-shadow: 0 0 10px var(--verde);
    }

    .pie {
        text-align: center;
        color: var(--verde-oscuro);
        font-size: 12px;
        margin-top: 30px;
        letter-spacing: 2px;
    }

</style>
""", unsafe_allow_html=True)

# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None


def get_mqtt_message(broker, port, topic, client_id):
    """Función para obtener un mensaje MQTT"""
    message_received = {"received": False, "payload": None}

    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            message_received["payload"] = payload
            message_received["received"] = True
        except:
            # Si no es JSON, guardar como texto
            message_received["payload"] = message.payload.decode()
            message_received["received"] = True

    try:
        client = mqtt.Client(client_id=client_id)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()

        # Esperar máximo 5 segundos
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)

        client.loop_stop()
        client.disconnect()

        return message_received["payload"]

    except Exception as e:
        return {"error": str(e)}


# ============================================================
# BARRA LATERAL
# ============================================================

with st.sidebar:
    st.subheader('🛰️ Panel de conexión')

    broker = st.text_input('Broker MQTT', value='broker.mqttdashboard.com',
                           help='Dirección del broker MQTT')

    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535,
                           help='Puerto del broker (generalmente 1883)')

    topic = st.text_input('Tópico', value='Sensor/THP2',
                          help='Tópico MQTT a suscribirse')

    client_id = st.text_input('ID del Cliente', value='streamlit_client',
                              help='Identificador único para este cliente')

# ============================================================
# TÍTULO
# ============================================================

st.title('📡 RADAR DE SEÑALES')
st.markdown(
    "<p class='subtitulo'>¡Capta los datos de tu sensor!</p>"
    "<div class='onda'>))) • (((</div>",
    unsafe_allow_html=True
)

# Información al inicio
with st.expander('📖 Manual de operación', expanded=False):
    st.markdown("""
    ### Cómo usar el radar:

    1. **Broker MQTT**: Ingresa la dirección del servidor MQTT en el panel lateral
    2. **Puerto**: Generalmente es 1883 para conexiones no seguras
    3. **Tópico**: El canal que quieres sintonizar
    4. **ID del Cliente**: Un identificador único para esta conexión
    5. Pulsa **Escanear señal** para recibir el mensaje más reciente

    ### Brokers públicos para pruebas:
    - broker.mqttdashboard.com
    - test.mosquitto.org
    - broker.hivemq.com
    """)

st.divider()

# ============================================================
# BOTÓN
# ============================================================

if st.button('🔄 Escanear señal', use_container_width=True):
    with st.spinner('📡 Sintonizando el broker y esperando señal...'):
        sensor_data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = sensor_data

# ============================================================
# RESULTADOS
# ============================================================

if st.session_state.sensor_data:
    st.divider()
    st.subheader('📊 Señal recibida')

    data = st.session_state.sensor_data

    # Verificar si hay error
    if isinstance(data, dict) and 'error' in data:
        st.error(f"❌ Señal perdida: {data['error']}")
    else:
        st.success('✅ Señal captada correctamente')

        # Mostrar datos en formato JSON
        if isinstance(data, dict):
            # Mostrar cada campo en una métrica
            cols = st.columns(len(data))
            for i, (key, value) in enumerate(data.items()):
                with cols[i]:
                    st.metric(label=key, value=value)

            # Mostrar JSON completo
            with st.expander('Ver JSON completo'):
                st.json(data)
        else:
            # Si no es diccionario, mostrar como texto
            st.code(data)

# ============================================================
# PIE DE PÁGINA
# ============================================================

st.markdown(
    "<div class='onda'>))) • (((</div>"
    "<p class='pie'>RADAR DE SEÑALES · escuchando el aire</p>",
    unsafe_allow_html=True
)
