from flask import Flask
from flask_socketio import SocketIO
import threading
import logging
from routes import app
from socketio_handlers import handle_connect, handle_disconnect, handle_light_toggle
from mqtt_client import mqtt_thread

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialise SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Register SocketIO event handlers
socketio.on_event("connect", handle_connect)
socketio.on_event("disconnect", handle_disconnect)
socketio.on_event("toggle_light", handle_light_toggle)

if __name__ == "__main__":
    # Start MQTT thread
    mqtt_thread = threading.Thread(target=mqtt_thread, daemon=True)
    mqtt_thread.start()

    socketio.run(app, host="127.0.0.1", port=5000, debug=True, use_reloader=True)
