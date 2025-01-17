from flask import Flask, render_template
from flask_basicauth import BasicAuth
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

load_dotenv(override=True)

app = Flask(__name__)
app.config["BASIC_AUTH_USERNAME"] = os.getenv("BASIC_AUTH_USERNAME")
app.config["BASIC_AUTH_PASSWORD"] = os.getenv("BASIC_AUTH_PASSWORD")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*")
basic_auth = BasicAuth(app)

@app.route("/")
@basic_auth.required
def index():
    return render_template("index.html")