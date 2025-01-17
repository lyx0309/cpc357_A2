from dotenv import load_dotenv
from flask_socketio import emit
import json
import logging
import paho.mqtt.client as mqtt
import os
import threading

load_dotenv(override=True)

# MQTT configuration
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
LIGHT_SWITCH_TOPIC = os.getenv("LIGHT_SWITCH_TOPIC")

logger = logging.getLogger(__name__)

temperature_data = []
humidity_data = []
data_lock = threading.Lock()
mqtt_client = None

def on_connect(client, userdata, flags, rc):
    logger.info(f"Code {rc}: Connected to MQTT broker")
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

        emit("update_data", 
             {"temperature": temperature_data,
              "humidity": humidity_data})
        logger.debug("Data emitted via Socket.IO")
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")


def on_connect_fail(client, userdata):
    logger.error("Failed to connect to MQTT broker")

def setup_mqtt_client():
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
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