# routes.py
from flask import render_template, current_app as app
from app import socketio
from flask_socketio import emit
from app.db import (
    init_db,
    store_message,
    get_message_history,
    clear_message_history,
    create_task,
    get_all_tasks,
    get_subtasks,
    get_task,
    update_task,
    delete_task,
    get_task_str
)
import app.ai.raven as raven
from tools.logging_utils import logger


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
    if message_content.startswith('/c'):
        clear_message_history(channel_id)
        emit('receive_message', {'type': 'clear'})
        return

    if message_content.startswith('/t'):
        tasks = get_all_tasks()
        if not tasks:
            create_task('New Task')
            tasks = get_all_tasks()
        formatted_tasks = [
            {
                'id': task['id'],
                'title': task['title'],
                'description': task['description'],
                'completed': bool(task['completed']),
                'dueDate': task['dueDate'],
                'parentID': task['parentID'],
            }
            for task in tasks
        ]
        emit('tasks_data', {'taskdata': {
             'name': 'My Tasks', 'tasks': formatted_tasks}})
        return

    store_message(channel_id, 'human', message_content)

    user_message = {'role': 'human', 'content': message_content}
    emit('receive_message', {'type': 'message', 'user_message': user_message})

    response_message = raven.general_chat_raven(
        get_message_history(channel_id))

    store_message(channel_id, 'ai', response_message)

    ai_message = {'role': 'ai', 'content': response_message}
    emit('receive_message', {'type': 'response', 'ai_message': ai_message})


@socketio.on('create_task')
def handle_create_task(data):
    title = data.get('title')
    description = data.get('description', '')
    completed = data.get('completed', False)
    dueDate = data.get('dueDate')
    parentID = data.get('parentID')

    if not title:
        emit('error', {'message': 'Task title is required.'})
        return

    task_id = create_task(title, description, completed, dueDate, parentID)
    new_task = get_task(task_id)
    formatted_task = {
        'id': new_task['id'],
        'title': new_task['title'],
        'description': new_task['description'],
        'completed': bool(new_task['completed']),
        'dueDate': new_task['dueDate'],
        'parentID': new_task['parentID'],
    }
    emit('task_created', {'task': formatted_task})


@socketio.on('update_task')
def handle_update_task(data):
    task_id = data.get('id')
    if not task_id:
        emit('error', {'message': 'Task ID is required.'})
        return

    title = data.get('title')
    description = data.get('description')
    completed = data.get('completed')
    dueDate = data.get('dueDate')
    parentID = data.get('parentID')

    success = update_task(task_id, title, description,
                          completed, dueDate, parentID)
    if success:
        updated_task = get_task(task_id)
        formatted_task = {
            'id': updated_task['id'],
            'title': updated_task['title'],
            'description': updated_task['description'],
            'completed': bool(updated_task['completed']),
            'dueDate': updated_task['dueDate'],
            'parentID': updated_task['parentID'],
        }
        emit('task_updated', {'task': formatted_task})
    else:
        emit('error', {'message': 'Task not found.'})


@socketio.on('delete_task')
def handle_delete_task(data):
    task_id = data.get('id')
    if not task_id:
        emit('error', {'message': 'Task ID is required.'})
        return

    success = delete_task(task_id)
    if success:
        emit('task_deleted', {'id': task_id})
    else:
        emit('error', {'message': 'Task not found.'})


@socketio.on('get_parent_tasks')
def handle_get_parent_tasks(data):
    parentID = data.get('parentID')
    parentTask = get_task(parentID)
    name = "My Tasks"
    if (parentTask['parentID'] is None):
        tasks = get_all_tasks()
    else:
        tasks = get_subtasks(parentTask.get('id'))
        name = parentTask['title']
    formatted_tasks = [
        {
            'id': task['id'],
            'title': task['title'],
            'description': task['description'],
            'completed': bool(task['completed']),
            'dueDate': task['dueDate'],
            'parentID': task['parentID'],
        }
        for task in tasks
    ]
    emit('tasks_data', {'taskdata': {
         'name': name, 'tasks': formatted_tasks}})


@socketio.on('get_sub_tasks')
def handle_get_sub_tasks(data):
    parentID = data.get('parentID')
    parentTask = get_task(parentID)
    tasks = get_subtasks(parentID)
    if not tasks:
        create_task('New Task', parentID=parentID)
        tasks = get_subtasks(parentID)
    formatted_tasks = [
        {
            'id': task['id'],
            'title': task['title'],
            'description': task['description'],
            'completed': bool(task['completed']),
            'dueDate': task['dueDate'],
            'parentID': task['parentID'],
        }
        for task in tasks
    ]
    emit('tasks_data', {'taskdata': {
         'name': parentTask['title'], 'tasks': formatted_tasks}})


@socketio.on('flip_tasks')
def handle_flip_tasks(data):
    task_id1 = data.get('id1')
    task_id2 = data.get('id2')
    task1 = get_task(task_id1)
    task2 = get_task(task_id2)
    update_task(task_id1, title=task2['title'], description=task2['description'], completed=task2['completed'],
                dueDate=task2['dueDate'], parentID=task2['parentID'])
    update_task(task_id2, title=task1['title'], description=task1['description'], completed=task1['completed'],
                dueDate=task1['dueDate'], parentID=task1['parentID'])
    taskName = "My Tasks"
    if task1['parentID'] is None:
        tasks = get_all_tasks()
    else:
        parentTask = get_task(task1['parentID'])
        tasks = get_subtasks(task1['parentID'])
        taskName = parentTask['title']
    formatted_tasks = [
        {
            'id': task['id'],
            'title': task['title'],
            'description': task['description'],
            'completed': bool(task['completed']),
            'dueDate': task['dueDate'],
            'parentID': task['parentID'],
        }
        for task in tasks
    ]
    emit('tasks_data', {'taskdata': {
         'name': taskName, 'tasks': formatted_tasks}})


@socketio.on('ai_message_task')
def handle_ai_message_task(data):
    tasks = data.get('tasks')
    logger.debug(f"Tasks: {tasks}")
    logger.debug(f"Message: {data.get('message')}")
    tasks_info = ""
    if tasks:
        for task in tasks:
            tasks_info += get_task_str(task)+'\n\n'
    response_message = raven.task_talk(data.get('message'), tasks_info)
    emit('ai_task_response', {'message': response_message})


if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True)
