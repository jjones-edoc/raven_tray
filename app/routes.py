from flask import render_template, current_app as app
from app import socketio
from flask_socketio import emit
from app.db import init_db, store_message, get_message_history, clear_message_history
import app.ai.raven as raven


@app.route('/')
def home():
    channel_id = 'general'  # Adjust as necessary
    messages = get_message_history(channel_id)
    return render_template('index.html', messages=messages, channel=channel_id)


@socketio.on('send_message')
def handle_send_message(data):
    channel_id = data['channel_id']
    message_content = data['message_content']

    if message_content == '':
        return
    if message_content == '/clear':
        clear_message_history(channel_id)
        emit('receive_message', {'type': 'clear'})
        return

    # Store the user message
    store_message(channel_id, 'human', message_content)

    # Emit the user's message
    user_message = {'role': 'human', 'content': message_content}
    emit('receive_message', {'type': 'message', 'user_message': user_message})

    response_message = raven.general_chat_raven(
        get_message_history(channel_id))

    # Generate and store the AI response
    store_message(channel_id, 'ai', response_message)

    # Emit the AI's response
    ai_message = {'role': 'ai', 'content': response_message}
    emit('receive_message', {'type': 'response', 'ai_message': ai_message})


if __name__ == '__main__':
    init_db()  # Initialize the database
    socketio.run(app, debug=True)
