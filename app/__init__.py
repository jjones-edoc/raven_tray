from flask import Flask
from flask_socketio import SocketIO
from .db import init_db

socketio = SocketIO()


def create_app():
    app = Flask(__name__)

    with app.app_context():
        # Import routes
        from . import routes

        init_db()
        # Initialize SocketIO
        socketio.init_app(app)

    return app
