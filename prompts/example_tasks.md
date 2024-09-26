### Example 1

human: how many tasks have been created

thoughts: The user is asking how many task are in the database. I will run a query to find out.

```python
query('SELECT COUNT(\*) as Total FROM tasks')
```

### Example 2

human: Can you change the description for first task to "do laundry"

thoughts: The user wants me to update the description for the first task. According to the information provided the task id is 1. I will run a sql command.

```python
command('UPDATE tasks SET description="do laundry" WHERE id="1"')
```
