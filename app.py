# app.py
from flask import Flask, render_template
from flask_basicauth import BasicAuth
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER = "34.172.246.156"
MQTT_PORT = 1883
MQTT_TOPIC = "iot"
LIGHT_SWITCH_TOPIC = "light_switch"

# Flask Configuration
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'YOUR_USERNAME'
app.config['BASIC_AUTH_PASSWORD'] = 'YOUR_VERY_SECURE_PASSWORD'
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
basic_auth = BasicAuth(app)

# MQTT Data
temperature_data = []
humidity_data = []
data_lock = threading.Lock()
mqtt_client = None  # Global client for publishing

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    logger.info(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global temperature_data, humidity_data
    try:
        data = json.loads(msg.payload.decode())
        logger.debug(f"Received MQTT message: {data}")
        
        with data_lock:
            temperature_data.append(data.get("temperature", 0))
            humidity_data.append(data.get("humidity", 0))
            
            if len(temperature_data) > 50:
                temperature_data = temperature_data[-50:]
            if len(humidity_data) > 50:
                humidity_data = humidity_data[-50:]
        
        socketio.emit('update_data', 
                     {'temperature': temperature_data, 
                      'humidity': humidity_data})
        logger.debug("Data emitted via Socket.IO")
        
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

# MQTT Client setup with error handling
def setup_mqtt_client():
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        
        def on_connect_fail(client, userdata):
            logger.error("Failed to connect to MQTT broker")
        client.on_connect_fail = on_connect_fail
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        return client
    except Exception as e:
        logger.error(f"Error setting up MQTT client: {e}")
        return None

def mqtt_thread():
    global mqtt_client
    mqtt_client = setup_mqtt_client()
    if mqtt_client:
        mqtt_client.loop_forever()
    else:
        logger.error("Failed to start MQTT thread")

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    with data_lock:
        emit('update_data', {
            'temperature': temperature_data,
            'humidity': humidity_data
        })

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")

@socketio.on('toggle_light')
def handle_light_toggle(data):
    try:
        state = data.get('state', 'off')
        logger.info(f"Publishing light state: {state}")
        if mqtt_client:
            mqtt_client.publish(LIGHT_SWITCH_TOPIC, state)
            emit('light_state', {'state': state}, broadcast=True)
        else:
            logger.error("MQTT client not available")
    except Exception as e:
        logger.error(f"Error publishing light state: {e}")

# Flask Route
@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Start MQTT thread
    mqtt_thread = threading.Thread(target=mqtt_thread, daemon=True)
    mqtt_thread.start()
    
    # Run Flask-SocketIO
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=False)
