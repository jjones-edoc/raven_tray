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
            title TEXT NOT NULL,
            description TEXT,  
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


def create_task(title, description='', completed=False, dueDate=None, parentID=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (title, description, completed, dueDate, parentID)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, int(completed), dueDate, parentID))
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


def update_task(task_id, title=None, description=None, completed=None, dueDate=None, parentID=None):
    conn = get_db_connection()
    c = conn.cursor()
    task = get_task(task_id)
    if not task:
        conn.close()
        return False  # Task not found

    # Update fields if provided
    new_title = title if title is not None else task['title']
    new_description = description if description is not None else task['description']
    new_completed = int(
        completed) if completed is not None else task['completed']

    # Set dueDate to NULL if it's None, otherwise keep the current value or the new value
    new_dueDate = None if dueDate is None else dueDate
    new_parentID = parentID if parentID is not None else task['parentID']

    # Execute the SQL query
    c.execute('''
        UPDATE tasks
        SET title = ?, description = ?, completed = ?, dueDate = ?, parentID = ?
        WHERE id = ?
    ''', (new_title, new_description, new_completed, new_dueDate, new_parentID, task_id))

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


def get_task_str(taskID):
    task = get_task(taskID)
    taskStr = f"Task ID: {task['id']}\nTitle: {task['title']}\nDescription: {task['description']}\nCompleted: {
        task['completed']}\nDue Date: {task['dueDate']}\nParent ID: {task['parentID']}"
    return taskStr


def db_query(sql, params=()):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(sql, params)
        rows = c.fetchall()
        if not rows:
            return "No results found."

        column_names = rows[0].keys()

        header = "| " + " | ".join(column_names) + " |"
        separator = "| " + " | ".join(['---'] * len(column_names)) + " |"

        table_rows = []
        for row in rows:
            row_data = "| " + \
                " | ".join(
                    str(row[col]) if row[col] is not None else "" for col in column_names) + " |"
            table_rows.append(row_data)

        markdown_table = "\n".join([header, separator] + table_rows)
        return markdown_table
    except sqlite3.Error as e:
        return f"An error occurred: {e}"
    finally:
        conn.close()


def db_command(sql, params=()):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(sql, params)
        conn.commit()
        rowcount = c.rowcount

        command_type = sql.strip().split()[0].upper()

        if command_type == "INSERT":
            message = f"{rowcount} item{
                's' if rowcount != 1 else ''} inserted."
        elif command_type == "UPDATE":
            message = f"{rowcount} item{'s' if rowcount != 1 else ''} updated."
        elif command_type == "DELETE":
            message = f"{rowcount} item{'s' if rowcount != 1 else ''} deleted."
        else:
            message = f"{rowcount} item{
                's' if rowcount != 1 else ''} affected."

        return message
    except sqlite3.Error as e:
        return f"An error occurred: {e}"
    finally:
        conn.close()
