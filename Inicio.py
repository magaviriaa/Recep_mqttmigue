import os
import json
import time
import streamlit as st
import paho.mqtt.client as mqtt

# Configuración de la página
st.set_page_config(
    page_title="Swiftie Sensor — MQTT",
    page_icon="📡",
    layout="centered"
)

# Estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

def get_mqtt_message(broker, port, topic, client_id):
    """Obtiene un mensaje (el primero que llegue) del tópico indicado."""
    message_received = {"received": False, "payload": None}

    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            message_received["payload"] = payload
        except Exception:
            message_received["payload"] = message.payload.decode()
        message_received["received"] = True

    try:
        client = mqtt.Client(client_id=client_id)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()

        # Esperar hasta 5 s a que llegue algo
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)

        client.loop_stop()
        client.disconnect()
        return message_received["payload"]

    except Exception as e:
        return {"error": str(e)}

# Sidebar - Configuración
with st.sidebar:
    st.subheader('⚙️ Conexión MQTT')
    broker = st.text_input('Broker MQTT', value='broker.mqttdashboard.com',
                           help='Servidor MQTT (p. ej. broker.mqttdashboard.com)')
    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535,
                           help='Usualmente 1883 (sin TLS)')
    topic = st.text_input('Tópico', value='Sensor/THP2',
                          help='Canal al que nos suscribimos (ej. Sensor/THP2)')
    client_id = st.text_input('ID del Cliente', value='streamlit_client',
                              help='Identificador único para esta conexión')

# Título
st.title('📡 Swiftie Sensor — MQTT (Taylor’s Version)')

with st.expander('ℹ️ Cómo usarlo', expanded=False):
    st.markdown("""
1) Configura **Broker**, **Puerto**, **Tópico** e **ID** en el panel lateral.  
2) Pulsa **Obtener Datos**: la app se suscribe y espera un mensaje hasta 5 s.  
3) Si llega JSON, te mostramos métricas; si es texto plano, lo verás en un bloque de código.  

**Brokers de prueba:** `broker.mqttdashboard.com`, `test.mosquitto.org`, `broker.hivemq.com`
""")

st.divider()

# Acción: obtener datos
if st.button('🔄 Obtener Datos del Sensor', use_container_width=True):
    with st.spinner('Conectando y esperando el próximo mensaje…'):
        sensor_data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = sensor_data

# Resultados
if st.session_state.sensor_data:
    st.divider()
    st.subheader('📊 Datos Recibidos')

    data = st.session_state.sensor_data

    if isinstance(data, dict) and 'error' in data:
        st.error(f"❌ Error de conexión: {data['error']}")
    else:
        st.success('✅ Mensaje recibido')
        if isinstance(data, dict):
            cols = st.columns(len(data))
            for i, (key, value) in enumerate(data.items()):
                with cols[i]:
                    st.metric(label=str(key), value=str(value))
            with st.expander('Ver JSON completo'):
                st.json(data)
        else:
            st.code(str(data))
