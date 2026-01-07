document.addEventListener("DOMContentLoaded", () => {
    const todoInput = document.getElementById("todo-input");
    const addButton = document.getElementById("add-button");
    const todoList = document.getElementById("todo-list");

    // Load todos from local storage
    let todos = JSON.parse(localStorage.getItem("todos")) || [];

    const saveTodos = () => {
        localStorage.setItem("todos", JSON.stringify(todos));
    };

    const renderTodos = () => {
        todoList.innerHTML = "";
        todos.forEach((todo, index) => {
            const li = document.createElement("li");
            li.className = todo.completed ? "completed" : "";
            li.innerHTML = `
                <span>${todo.text}</span>
                <div>
                    <button class="complete-button" data-index="${index}">${todo.completed ? "Uncomplete" : "Complete"}</button>
                    <button class="delete-button" data-index="${index}">Delete</button>
                </div>
            `;
            todoList.appendChild(li);
        });
    };

    const addTodo = () => {
        const todoText = todoInput.value.trim();
        if (todoText !== "") {
            todos.push({ text: todoText, completed: false });
            todoInput.value = "";
            saveTodos();
            renderTodos();
        }
    };

    const toggleComplete = (index) => {
        todos[index].completed = !todos[index].completed;
        saveTodos();
        renderTodos();
    };

    const deleteTodo = (index) => {
        todos.splice(index, 1);
        saveTodos();
        renderTodos();
    };

    addButton.addEventListener("click", addTodo);

    todoInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            addTodo();
        }
    });

    todoList.addEventListener("click", (e) => {
        if (e.target.classList.contains("complete-button")) {
            const index = e.target.dataset.index;
            toggleComplete(index);
        } else if (e.target.classList.contains("delete-button")) {
            const index = e.target.dataset.index;
            deleteTodo(index);
        }
    });

    renderTodos();
});
