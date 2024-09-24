// task.js

class TaskList {
  constructor(config) {
    this.container = config.container; // HTML element to render into
    this.taskData = config.taskData; // Initial tasks data
    this.parentID = null; // Tracks current parent task for subtasks
    this.currentTaskIdForDate = null; // Tracks task ID for due date editing
    this.socket = config.socket; // Socket.io instance

    this.init();
  }

  init() {
    this.render();
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Add Task Button
    const addTaskBtn = this.container.querySelector(".add-task-btn");
    addTaskBtn.addEventListener("click", () => this.handleAddTask());

    // Back Button
    const backBtn = this.container.querySelector(".back-btn");
    backBtn.addEventListener("click", () => this.handleGoBack());

    // Close Button
    const closeBtn = this.container.querySelector(".close-card-btn");
    closeBtn.addEventListener("click", () => this.handleClose());

    // Chat Send Button
    const sendMessageBtn = this.container.querySelector(".send-message-btn");
    const chatInput = this.container.querySelector(".chat-input");
    sendMessageBtn.addEventListener("click", () => this.handleSendMessage());
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.handleSendMessage();
    });

    // Modal Buttons
    const saveDateBtn = this.container.querySelector(".save-date-btn");
    const clearDateBtn = this.container.querySelector(".clear-date-btn");
    saveDateBtn.addEventListener("click", () => this.handleSaveDueDate());
    clearDateBtn.addEventListener("click", () => this.handleClearDueDate());
  }

  render() {
    this.container.innerHTML = `
        <div class="task-card">
          <!-- Header with Title, Add Task Button, Back Button, and Close Button -->
          <div class="task-header mb-3 d-flex justify-content-between align-items-center">
            <h1 class="task-title">${this.taskData.name}</h1>
            <div>
              <button class="icon-btn back-btn d-none" title="Back to Parent Task">
                <i class="fas fa-arrow-left"></i>
              </button>
              <button class="icon-btn add-task-btn" title="Add Task">
                <i class="fas fa-plus"></i>
              </button>
              <button class="icon-btn close-card-btn" title="Close">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
  
          <ul class="list-group task-list"></ul>
  
          <!-- Chatbot interaction -->
          <div class="chat-container d-none">
            <!-- Messages will appear here -->
          </div>
  
          <div class="chat-input-container">
            <input type="text" class="form-control chat-input me-1" placeholder="Type a message..." />
            <button class="btn btn-primary send-message-btn">Send</button>
          </div>
        </div>
  
        <!-- Date Picker Modal -->
        <div class="modal fade date-picker-modal" tabindex="-1" aria-hidden="true">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Set Due Date</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">
                <input type="text" class="form-control due-date-input" placeholder="Select due date" />
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary clear-date-btn">Clear Date</button>
                <button type="button" class="btn btn-primary save-date-btn">Save</button>
              </div>
            </div>
          </div>
        </div>
      `;

    this.taskListElement = this.container.querySelector(".task-list");
    this.chatContainer = this.container.querySelector(".chat-container");
    this.chatInput = this.container.querySelector(".chat-input");
    this.datePickerModalElement = this.container.querySelector(".date-picker-modal");
    this.dueDateInput = this.container.querySelector(".due-date-input");
    this.taskTitleElement = this.container.querySelector(".task-title");
    this.backBtn = this.container.querySelector(".back-btn");
    this.addTaskBtn = this.container.querySelector(".add-task-btn");

    // Initialize Flatpickr
    this.fp = flatpickr(this.dueDateInput, {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
    });

    // Initialize Bootstrap Modal
    this.datePickerModal = new bootstrap.Modal(this.datePickerModalElement);

    // Initialize SortableJS
    this.sortable = new Sortable(this.taskListElement, {
      handle: ".drag-handle",
      animation: 150,
      group: "tasks",
      ghostClass: "sortable-ghost",
      onEnd: (evt) => this.updateTaskOrder(evt),
    });

    this.renderTasks(this.taskData.tasks);
  }

  updateTask(taskId, updatedData) {
    const task = this.findTaskById(taskId, this.taskData.tasks);
    if (task) {
      this.socket.emit("update_task", { id: taskId, ...updatedData });
    }
  }

  deleteTask(taskId) {
    this.socket.emit("delete_task", { id: taskId });
  }

  renderTasks(tasks) {
    this.taskListElement.innerHTML = "";

    tasks.forEach((task) => {
      this.parentID = task.parentID;
      const taskItem = document.createElement("li");
      taskItem.className = "list-group-item w-100 ps-2";
      taskItem.dataset.id = task.id;

      const taskContent = document.createElement("div");
      taskContent.className = "task-content d-flex align-items-center justify-content-between w-100";

      const leftContainer = document.createElement("div");
      leftContainer.className = "d-flex align-items-center w-100";

      const dragHandle = document.createElement("span");
      dragHandle.className = "drag-handle me-2";
      dragHandle.innerHTML = '<i class="fas fa-grip-lines-vertical"></i>';
      dragHandle.style.cursor = "grab";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "form-check-input me-2";
      checkbox.checked = task.completed;
      checkbox.addEventListener("change", (e) => this.toggleComplete(e, task.id));

      const taskInput = document.createElement("input");
      taskInput.type = "text";
      taskInput.className = "form-control me-2 w-100";
      taskInput.value = task.info;
      taskInput.style.flexGrow = "1";
      taskInput.style.minWidth = "0";
      taskInput.addEventListener("change", (e) => this.updateTaskName(task.id, e.target.value));

      leftContainer.appendChild(dragHandle);
      leftContainer.appendChild(checkbox);
      leftContainer.appendChild(taskInput);

      const taskActions = document.createElement("div");
      taskActions.className = "task-actions d-flex gap-2";

      // Date Icon or Due Date Badge
      if (task.dueDate) {
        const dueDateBadge = document.createElement("span");
        dueDateBadge.className = "badge bg-info text-dark due-date-badge";
        dueDateBadge.textContent = this.formatDate(task.dueDate);
        dueDateBadge.title = "Click to edit due date";
        dueDateBadge.addEventListener("click", () => this.openDatePicker(task.id));
        taskActions.appendChild(dueDateBadge);
      } else {
        const dateBtn = document.createElement("button");
        dateBtn.className = "icon-btn";
        dateBtn.title = "Set Due Date";
        dateBtn.innerHTML = '<i class="fas fa-calendar-alt"></i>';
        dateBtn.addEventListener("click", () => this.openDatePicker(task.id));
        taskActions.appendChild(dateBtn);
      }

      // Subtasks and Delete Buttons
      const viewSubtasksBtn = document.createElement("button");
      viewSubtasksBtn.className = "btn btn-sm btn-success";
      viewSubtasksBtn.title = "View Subtasks";
      viewSubtasksBtn.innerHTML = '<i class="fas fa-arrow-right"></i>';
      viewSubtasksBtn.addEventListener("click", () => this.viewSubtasks(task.id));

      const deleteBtn = document.createElement("button");
      deleteBtn.className = "btn btn-sm btn-danger";
      deleteBtn.title = "Delete Task";
      deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
      deleteBtn.addEventListener("click", () => this.deleteTask(task.id));

      taskActions.appendChild(viewSubtasksBtn);
      taskActions.appendChild(deleteBtn);

      taskContent.appendChild(leftContainer);
      taskContent.appendChild(taskActions);

      taskItem.appendChild(taskContent);
      this.taskListElement.appendChild(taskItem);
    });
    if (this.parentID) {
      this.container.querySelector(".back-btn").classList.remove("d-none");
    } else {
      this.container.querySelector(".back-btn").classList.add("d-none");
    }
  }

  handleAddTask() {
    this.socket.emit("create_task", {
      id: new Date().getTime(),
      info: "New Task",
      completed: false,
      dueDate: null,
      parentID: this.parentID ? this.parentID : null,
    });
  }

  handleGoBack() {
    if (this.parentID) {
      this.socket.emit("get_parent_tasks", { parentID: this.parentID });
    }
  }

  handleClose() {
    this.container.style.display = "none";
  }

  handleSendMessage() {
    const message = this.chatInput.value.trim();
    if (message === "") return;

    this.displayMessage(message, "user-message");
    this.chatInput.value = "";

    if (this.chatContainer.classList.contains("d-none")) {
      this.chatContainer.classList.remove("d-none");
    }

    // Call the external AI message handler
    this.onMessageAI(message, (aiResponse) => {
      this.displayMessage(aiResponse, "ai-message");
    });
  }

  displayMessage(message, className) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${className}`;
    messageDiv.textContent = message;
    this.chatContainer.appendChild(messageDiv);
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }

  viewSubtasks(taskId) {
    this.socket.emit("get_sub_tasks", { parentID: taskId });
  }

  toggleComplete(event, taskId) {
    const completed = event.target.checked;
    this.updateTask(taskId, { completed });
  }

  updateTaskName(taskId, newName) {
    this.updateTask(taskId, { info: newName });
  }

  openDatePicker(taskId) {
    this.currentTaskIdForDate = taskId;
    const task = this.findTaskById(taskId, this.taskData.tasks);
    if (task && task.dueDate) {
      this.fp.setDate(new Date(task.dueDate));
    } else {
      this.fp.clear();
    }
    this.datePickerModal.show();
  }

  handleSaveDueDate() {
    const selectedDate = this.dueDateInput.value;
    if (this.currentTaskIdForDate !== null) {
      const updatedData = selectedDate ? { dueDate: new Date(selectedDate).toISOString() } : { dueDate: null };
      this.updateTask(this.currentTaskIdForDate, updatedData);
    }
    this.datePickerModal.hide();
  }

  handleClearDueDate() {
    if (this.currentTaskIdForDate !== null) {
      this.updateTask(this.currentTaskIdForDate, { dueDate: null });
    }
    this.datePickerModal.hide();
  }

  formatDate(dateString) {
    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, options);
  }

  findTaskById(taskId, taskArray) {
    for (let task of taskArray) {
      if (task.id === taskId) return task;
      if (task.subtasks && task.subtasks.length > 0) {
        const found = this.findTaskById(taskId, task.subtasks);
        if (found) return found;
      }
    }
    return null;
  }

  updateTaskOrder(evt) {
    const movedTaskId = parseInt(evt.item.dataset.id, 10);
    const newIndex = evt.newIndex;

    let currentTasks = this.taskData.tasks;

    // Remove the task from its current position
    const movedTask = currentTasks.find((task) => task.id === movedTaskId);
    currentTasks = currentTasks.filter((task) => task.id !== movedTaskId);

    // Insert the task at the new position
    currentTasks.splice(newIndex, 0, movedTask);

    // Update the tasks array
    this.taskData.tasks = currentTasks;

    this.renderTasks(this.taskData.tasks);
  }
}

// Export the TaskList class if using modules
// Uncomment the line below if using a module system
// export default TaskList;
