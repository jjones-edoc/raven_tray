import sqlite3


def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def store_message(channel_id, role, content):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO messages (channel_id, role, content)
        VALUES (?, ?, ?)
    ''', (channel_id, role, content))
    conn.commit()
    conn.close()


def get_message_history(channel_id):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''
        SELECT role, content FROM messages
        WHERE channel_id = ?
        ORDER BY id ASC
    ''', (channel_id,))
    messages = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    return messages


def clear_message_history(channel_id=None):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()

    if channel_id:
        c.execute('DELETE FROM messages WHERE channel_id = ?', (channel_id,))
    else:
        c.execute('DELETE FROM messages')

    conn.commit()
    conn.close()
