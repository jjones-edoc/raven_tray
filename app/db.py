# db.py
import sqlite3
from datetime import datetime

DATABASE = 'chat_history.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            info TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            dueDate TEXT,
            parentID INTEGER,
            FOREIGN KEY(parentID) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

# Chat Functions


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

# Tasks Functions


def create_task(info, completed=False, dueDate=None, parentID=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (info, completed, dueDate, parentID)
        VALUES (?, ?, ?, ?)
    ''', (info, int(completed), dueDate, parentID))
    conn.commit()
    task_id = c.lastrowid
    conn.close()
    return task_id


def get_task(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_all_tasks():
    # get all tasks that are not subtasks
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE parentID IS NULL ORDER BY id ASC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_task(task_id, info=None, completed=None, dueDate=None, parentID=None):
    conn = get_db_connection()
    c = conn.cursor()
    task = get_task(task_id)
    if not task:
        conn.close()
        return False  # Task not found

    # Update fields if provided
    new_info = info if info is not None else task['info']
    new_completed = int(
        completed) if completed is not None else task['completed']
    new_dueDate = dueDate if dueDate is not None else task['dueDate']
    new_parentID = parentID if parentID is not None else task['parentID']

    c.execute('''
        UPDATE tasks
        SET info = ?, completed = ?, dueDate = ?, parentID = ?
        WHERE id = ?
    ''', (new_info, new_completed, new_dueDate, new_parentID, task_id))
    conn.commit()
    conn.close()
    return True


def delete_task(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE parentID = ?', (task_id,))
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    changes = c.rowcount
    conn.close()
    return changes > 0  # Returns True if a row was deleted


def get_subtasks(parent_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE parentID = ? ORDER BY id ASC', (parent_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
