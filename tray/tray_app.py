import threading
import webbrowser
from flask import Flask
from PIL import Image
import pystray
from pystray import MenuItem as item

from app import create_app, socketio

# Function to start Flask app


def run_flask():
    app = create_app()
    app.run(port=5000)
    socketio.run(app)

# Function to open the web page


def open_webpage(icon, item):
    webbrowser.open("http://127.0.0.1:5000")

# Function to quit the tray app


def on_quit(icon, item):
    icon.stop()


# Load the tray icon image
image = Image.open("tray/assets/tray_icon.png")

# Define the icon and menu
icon = pystray.Icon("Raven")
icon.icon = image
icon.menu = pystray.Menu(
    item('Open Web Interface', open_webpage),
    item('Quit', on_quit)
)

# Run the Flask app in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# Run the tray icon
icon.run()
