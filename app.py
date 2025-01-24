# app.py
from flask import Flask, render_template, g
from flask_basicauth import BasicAuth
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import os
import threading
import logging
from dotenv import load_dotenv
from database import get_db, init_app, query_db

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
LIGHT_SWITCH_TOPIC = os.getenv("LIGHT_SWITCH_TOPIC")

# Flask Configuration
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = os.getenv("BASIC_AUTH_USERNAME")
app.config['BASIC_AUTH_PASSWORD'] = os.getenv("BASIC_AUTH_PASSWORD")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
basic_auth = BasicAuth(app)

# Initialize the database
init_app(app)

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
        
        temperature = data.get("temperature", 0)
        humidity = data.get("humidity", 0)
        
        with data_lock:
            temperature_data.append(temperature)
            humidity_data.append(humidity)
            
            if len(temperature_data) > 50:
                temperature_data = temperature_data[-50:]
            if len(humidity_data) > 50:
                humidity_data = humidity_data[-50:]
        
        emit('update_data', 
             {'temperature': temperature_data, 
              'humidity': humidity_data})
        logger.debug("Data emitted via Socket.IO")
        
        # Insert data into the database within the app context
        with app.app_context():
            db = get_db()
            db.execute("INSERT INTO sensor_data (temperature, humidity) VALUES (?, ?)", (temperature, humidity))
            db.commit()
        
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

@app.route('/data')
@basic_auth.required
def data():
    db = get_db()
    sensor_data = query_db("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 50")
    return render_template('data.html', sensor_data=sensor_data)

if __name__ == '__main__':
    # Start MQTT thread
    mqtt_thread = threading.Thread(target=mqtt_thread, daemon=True)
    mqtt_thread.start()
    
    # Run Flask-SocketIO
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=True)
