from flask_socketio import emit
from mqtt_client import mqtt_client, LIGHT_SWITCH_TOPIC, temperature_data, humidity_data, data_lock
import logging

logger = logging.getLogger(__name__)

def handle_connect():
    logger.info("Client connected")
    with data_lock:
        emit("update_data", {
            "temperature": temperature_data,
            "humidity": humidity_data
        })

def handle_disconnect():
    logger.info("Client disconnected")

def handle_light_toggle(data):
    try:
        state = data.get("state", "off")
        logger.info(f"Publishing light state: {state}")
        if mqtt_client:
            mqtt_client.publish(LIGHT_SWITCH_TOPIC, state)
            emit("light_state", {"state": state}, broadcast=True)
        else:
            logger.error("MQTT Client unavailable")
    except Exception as e:
        logger.error(f"Error publishing light state: {e}")