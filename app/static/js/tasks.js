// task.js

class TaskList {
  constructor({ container, taskData, socket }) {
    this.container = container; // HTML element to render into
    this.taskData = taskData; // Initial tasks data
    this.parentID = null; // Tracks current parent task for subtasks
    this.currentTaskIdForDate = null; // Tracks task ID for due date editing
    this.socket = socket; // Socket.io instance

    this.init();
  }

  init() {
    this.render();
    this.setupEventListeners();
    this.setupSocketListeners();
  }

  setupEventListeners() {
    const { addTaskBtn, backBtn, closeBtn, sendMessageBtn, chatInput, saveDateBtn, clearDateBtn } = this.getCommonElements();

    addTaskBtn.addEventListener("click", this.handleAddTask);
    backBtn.addEventListener("click", this.handleGoBack);
    closeBtn.addEventListener("click", this.handleClose);

    sendMessageBtn.addEventListener("click", this.handleSendMessage);
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.handleSendMessage();
    });

    saveDateBtn.addEventListener("click", this.handleSaveDueDate);
    clearDateBtn.addEventListener("click", this.handleClearDueDate);
  }

  setupSocketListeners() {
    // Listen for task updates from the server
    this.socket.on("tasks_updated", (updatedTaskData) => {
      this.taskData = updatedTaskData;
      this.renderTasks(this.taskData.tasks);
      this.toggleBackButton();
      this.updateTaskTitle();
    });
  }

  getCommonElements() {
    return {
      addTaskBtn: this.container.querySelector(".add-task-btn"),
      backBtn: this.container.querySelector(".back-btn"),
      closeBtn: this.container.querySelector(".close-card-btn"),
      sendMessageBtn: this.container.querySelector(".send-message-btn"),
      chatInput: this.container.querySelector(".chat-input"),
      saveDateBtn: this.container.querySelector(".save-date-btn"),
      clearDateBtn: this.container.querySelector(".clear-date-btn"),
    };
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
          <div class="chat-container d-none"></div>
  
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

    this.cacheDOMElements();
    this.initializePlugins();
    this.renderTasks(this.taskData.tasks);
    this.toggleBackButton();
  }

  cacheDOMElements() {
    this.taskListElement = this.container.querySelector(".task-list");
    this.chatContainer = this.container.querySelector(".chat-container");
    this.chatInput = this.container.querySelector(".chat-input");
    this.datePickerModalElement = this.container.querySelector(".date-picker-modal");
    this.dueDateInput = this.container.querySelector(".due-date-input");
    this.taskTitleElement = this.container.querySelector(".task-title");
    this.backBtn = this.container.querySelector(".back-btn");
    this.addTaskBtn = this.container.querySelector(".add-task-btn");
  }

  initializePlugins() {
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
      onEnd: this.updateTaskOrder,
    });
  }

  toggleBackButton() {
    if (this.parentID !== null) {
      this.backBtn.classList.remove("d-none");
    } else {
      this.backBtn.classList.add("d-none");
    }
  }

  updateTaskTitle() {
    this.taskTitleElement.textContent = this.taskData.name;
  }

  renderTasks(tasks) {
    this.taskListElement.innerHTML = "";

    tasks.forEach((task) => {
      this.parentID = task.parentID;
      const taskItem = this.createTaskElement(task);
      this.taskListElement.appendChild(taskItem);
    });

    this.toggleBackButton();
  }

  createTaskElement(task) {
    const taskItem = document.createElement("li");
    taskItem.className = "list-group-item w-100 ps-2";
    taskItem.dataset.id = task.id;

    const taskContent = document.createElement("div");
    taskContent.className = "task-content d-flex align-items-center justify-content-between w-100";

    // Left Container: Drag Handle, Checkbox, Task Input
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
    taskInput.value = task.title;
    taskInput.style.flexGrow = "1";
    taskInput.style.minWidth = "0";
    taskInput.addEventListener("change", (e) => this.updateTaskName(task.id, e.target.value));

    leftContainer.append(dragHandle, checkbox, taskInput);

    // Add description area
    const descriptionContainer = document.createElement("div");
    descriptionContainer.className = "description-container mt-2";

    const descriptionDisplay = document.createElement("p");
    descriptionDisplay.className = "task-description mb-0";
    descriptionDisplay.textContent = task.description || "";
    descriptionDisplay.style.cursor = "pointer";
    descriptionDisplay.addEventListener("click", () => this.openDescriptionEditor(task.id));

    const descriptionEditor = document.createElement("textarea");
    descriptionEditor.className = "form-control task-description-editor d-none";
    descriptionEditor.value = task.description || "";
    descriptionEditor.addEventListener("blur", () => this.saveTaskDescription(task.id, descriptionEditor.value));

    descriptionContainer.append(descriptionDisplay, descriptionEditor);

    if (!task.description) {
      descriptionContainer.classList.add("d-none"); // Hide description if it's empty
    }

    // Right Container: Due Date, Subtasks, Delete, Add Description
    const taskActions = document.createElement("div");
    taskActions.className = "task-actions d-flex gap-2";

    // Add Description Button with consistent icon styling
    if (!task.description) {
      const addDescriptionBtn = document.createElement("button");
      addDescriptionBtn.className = "icon-btn btn-sm"; // Consistent class
      addDescriptionBtn.title = "Add Description";
      addDescriptionBtn.innerHTML = '<i class="fas fa-pencil-alt"></i>'; // Font Awesome icon for editing
      addDescriptionBtn.addEventListener("click", () => this.addDescription(task.id));
      taskActions.appendChild(addDescriptionBtn);
    }

    // Due Date Button or Badge with consistent icon styling
    if (task.dueDate) {
      const dueDateBadge = this.createDueDateBadge(task);
      taskActions.appendChild(dueDateBadge);
    } else {
      const dateBtn = this.createDateButton(task.id);
      dateBtn.className = "icon-btn btn-sm"; // Apply consistent class
      taskActions.appendChild(dateBtn);
    }

    // Subtasks Button with consistent icon styling
    const viewSubtasksBtn = this.createSubtasksButton(task.id);
    viewSubtasksBtn.className = "icon-btn btn-sm"; // Apply consistent class
    taskActions.appendChild(viewSubtasksBtn);

    // Delete Button with consistent icon styling
    const deleteBtn = this.createDeleteButton(task.id);
    deleteBtn.className = "icon-btn btn-sm btn-danger"; // Apply consistent class, add danger for delete
    taskActions.appendChild(deleteBtn);

    taskContent.append(leftContainer, taskActions);
    taskItem.append(taskContent, descriptionContainer); // Add description to task item

    return taskItem;
  }

  addDescription(taskId) {
    const taskElement = this.taskListElement.querySelector(`[data-id='${taskId}']`);
    const descriptionContainer = taskElement.querySelector(".description-container");
    const descriptionEditor = taskElement.querySelector(".task-description-editor");
    const descriptionDisplay = taskElement.querySelector(".task-description");

    descriptionContainer.classList.remove("d-none"); // Show description container
    descriptionDisplay.classList.add("d-none");
    descriptionEditor.classList.remove("d-none");
    descriptionEditor.focus(); // Automatically focus on the editor
  }

  openDescriptionEditor(taskId) {
    const taskElement = this.taskListElement.querySelector(`[data-id='${taskId}']`);
    const descriptionDisplay = taskElement.querySelector(".task-description");
    const descriptionEditor = taskElement.querySelector(".task-description-editor");

    descriptionDisplay.classList.add("d-none");
    descriptionEditor.classList.remove("d-none");
    descriptionEditor.focus(); // Automatically focus on the editor
  }

  saveTaskDescription(taskId, newDescription) {
    this.updateTask(taskId, { description: newDescription });

    // Revert back to the display mode
    const taskElement = this.taskListElement.querySelector(`[data-id='${taskId}']`);
    const descriptionDisplay = taskElement.querySelector(".task-description");
    const descriptionEditor = taskElement.querySelector(".task-description-editor");
    const addDescriptionBtn = taskElement.querySelector(".btn-secondary");

    if (newDescription) {
      descriptionDisplay.textContent = newDescription;
      addDescriptionBtn?.remove(); // Remove the Add Description button
    } else {
      descriptionDisplay.textContent = "";
    }

    descriptionEditor.classList.add("d-none");
    descriptionDisplay.classList.remove("d-none");
  }

  createDueDateBadge(task) {
    const dueDateBadge = document.createElement("span");
    dueDateBadge.className = "badge bg-info text-dark due-date-badge";
    dueDateBadge.textContent = this.formatDate(task.dueDate);
    dueDateBadge.title = "Click to edit due date";
    dueDateBadge.style.cursor = "pointer";
    dueDateBadge.addEventListener("click", () => this.openDatePicker(task.id));
    return dueDateBadge;
  }

  createDateButton(taskId) {
    const dateBtn = document.createElement("button");
    dateBtn.className = "icon-btn";
    dateBtn.title = "Set Due Date";
    dateBtn.innerHTML = '<i class="fas fa-calendar-alt"></i>';
    dateBtn.style.cursor = "pointer";
    dateBtn.addEventListener("click", () => this.openDatePicker(taskId));
    return dateBtn;
  }

  createSubtasksButton(taskId) {
    const viewSubtasksBtn = document.createElement("button");
    viewSubtasksBtn.className = "btn btn-sm btn-success";
    viewSubtasksBtn.title = "View Subtasks";
    viewSubtasksBtn.innerHTML = '<i class="fas fa-arrow-right"></i>';
    viewSubtasksBtn.addEventListener("click", () => this.viewSubtasks(taskId));
    return viewSubtasksBtn;
  }

  createDeleteButton(taskId) {
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "btn btn-sm btn-danger";
    deleteBtn.title = "Delete Task";
    deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
    deleteBtn.style.cursor = "pointer";
    deleteBtn.addEventListener("click", () => this.deleteTask(taskId));
    return deleteBtn;
  }

  handleAddTask = () => {
    const newTask = {
      id: Date.now(),
      title: "New Task",
      description: "",
      completed: false,
      dueDate: null,
      parentID: this.parentID, // Assign current parentID if any
    };
    this.socket.emit("create_task", newTask);
  };

  handleGoBack = () => {
    if (this.parentID === null) return; // Already at top-level
    this.socket.emit("get_parent_tasks", { parentID: this.parentID });
  };

  handleClose = () => {
    this.container.style.display = "none";
  };

  handleSendMessage = () => {
    const message = this.chatInput.value.trim();
    if (!message) return;

    this.displayMessage(message, "user-message");
    this.chatInput.value = "";

    if (this.chatContainer.classList.contains("d-none")) {
      this.chatContainer.classList.remove("d-none");
    }
    let task_ids = [];
    for (const task of this.taskData.tasks) {
      task_ids.push(task.id);
    }
    this.socket.emit("ai_message_task", { message, tasks: task_ids });
  };

  displayMessage(message, className) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${className}`;
    messageDiv.textContent = message;
    this.chatContainer.appendChild(messageDiv);
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }

  viewSubtasks = (taskId) => {
    this.socket.emit("get_sub_tasks", { parentID: taskId });
  };

  toggleComplete = (event, taskId) => {
    const completed = event.target.checked;
    this.updateTask(taskId, { completed });
  };

  updateTaskName(taskId, newName) {
    this.updateTask(taskId, { title: newName });
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

  handleSaveDueDate = () => {
    const selectedDate = this.dueDateInput.value;
    if (this.currentTaskIdForDate !== null) {
      const updatedData = selectedDate ? { dueDate: new Date(selectedDate).toISOString() } : { dueDate: null };
      this.updateTask(this.currentTaskIdForDate, updatedData);
    }
    this.datePickerModal.hide();
  };

  handleClearDueDate = () => {
    if (this.currentTaskIdForDate !== null) {
      this.updateTask(this.currentTaskIdForDate, { dueDate: null });
    }
    this.datePickerModal.hide();
  };

  updateTask(taskId, updatedData) {
    this.socket.emit("update_task", { id: taskId, ...updatedData });
  }

  deleteTask(taskId) {
    this.socket.emit("delete_task", { id: taskId });
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

  findTaskById(taskId, tasks) {
    for (const task of tasks) {
      if (task.id === taskId) return task;
      if (task.subtasks && task.subtasks.length > 0) {
        const found = this.findTaskById(taskId, task.subtasks);
        if (found) return found;
      }
    }
    return null;
  }

  updateTaskOrder = (evt) => {
    const movedTaskId = Number(evt.item.dataset.id);
    const newIndex = evt.newIndex;

    const currentTasks = [...this.taskData.tasks];
    const movedTaskIndex = currentTasks.findIndex((task) => task.id === movedTaskId);
    if (movedTaskIndex === -1) return;

    const [movedTask] = currentTasks.splice(movedTaskIndex, 1);
    this.socket.emit("flip_tasks", { id1: movedTaskId, id2: currentTasks[newIndex].id });
  };
}
