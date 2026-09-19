const STORAGE_KEY = "vision-control-demo-state";

const initialState = {
  employees: [
    { id: 1, name: "Алексей Иванов", position: "Системный аналитик", email: "ivanov@example.com", phone: "+7 900 111 22 33" },
    { id: 2, name: "Марина Петрова", position: "Оператор", email: "petrova@example.com", phone: "+7 900 333 44 55" }
  ],
  positions: [
    { id: 1, title: "Оператор", department: "Операционный центр", level: "Middle" },
    { id: 2, title: "Системный аналитик", department: "ИТ", level: "Senior" }
  ],
  biometrics: [
    { id: 1, name: "Алексей Иванов", template: "Face-01", status: "Активен" },
    { id: 2, name: "Марина Петрова", template: "Face-02", status: "Ожидание" }
  ]
};

const state = loadState();

let streamSocket = null;
let frameCounter = 0;
let streamCanvas = null;
let streamCtx = null;
let streamImage = null;
let currentObjectUrl = null;

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return JSON.parse(JSON.stringify(initialState));
    }
    return JSON.parse(raw);
  } catch {
    return JSON.parse(JSON.stringify(initialState));
  }
}

function persistState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function switchView(viewName) {
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === `${viewName}View`);
  });

  document.querySelectorAll(".nav-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewName);
  });

  const titles = {
    stream: "Трансляция",
    employees: "Сотрудники",
    positions: "Должности",
    biometrics: "Биометрия"
  };

  document.getElementById("pageTitle").textContent = titles[viewName];
}

function renderEmployees() {
  const body = document.getElementById("employeesTableBody");
  if (!body) return;

  if (!state.employees.length) {
    body.innerHTML = `<tr><td colspan="4" style="color: var(--muted);">Нет данных</td></tr>`;
    return;
  }

  body.innerHTML = state.employees
    .map((employee) => `
      <tr>
        <td>${escapeHtml(employee.name)}</td>
        <td>${escapeHtml(employee.position)}</td>
        <td>${escapeHtml(employee.email)}</td>
        <td>${escapeHtml(employee.phone)}</td>
      </tr>
    `)
    .join("");
}

function renderPositions() {
  const body = document.getElementById("positionsTableBody");
  if (!body) return;

  if (!state.positions.length) {
    body.innerHTML = `<tr><td colspan="3" style="color: var(--muted);">Нет данных</td></tr>`;
    return;
  }

  body.innerHTML = state.positions
    .map((position) => `
      <tr>
        <td>${escapeHtml(position.title)}</td>
        <td>${escapeHtml(position.department)}</td>
        <td>${escapeHtml(position.level)}</td>
      </tr>
    `)
    .join("");
}

function renderBiometrics() {
  const body = document.getElementById("biometricsTableBody");
  if (!body) return;

  if (!state.biometrics.length) {
    body.innerHTML = `<tr><td colspan="3" style="color: var(--muted);">Нет данных</td></tr>`;
    return;
  }

  body.innerHTML = state.biometrics
    .map((item) => `
      <tr>
        <td>${escapeHtml(item.name)}</td>
        <td>${escapeHtml(item.template)}</td>
        <td>${escapeHtml(item.status)}</td>
      </tr>
    `)
    .join("");
}

function renderAll() {
  renderEmployees();
  renderPositions();
  renderBiometrics();
}

function setStreamStatus(message, connected) {
  const badge = document.getElementById("streamBadge");
  const text = document.getElementById("streamMessage");
  const connectionState = document.getElementById("connectionState");
  const serviceStatus = document.getElementById("serviceStatus");
  const sidebarStatus = document.getElementById("sidebarStatus");
  const topbarStatus = document.getElementById("topbarStatus");

  if (connected) {
    badge.className = "badge badge-success";
    badge.textContent = "Подключено";
    connectionState.textContent = "Online";
    serviceStatus.textContent = "Трансляция активна";
    sidebarStatus.textContent = "Трансляция работает";
    topbarStatus.textContent = "Подключение стабильно";
  } else {
    badge.className = "badge badge-warning";
    badge.textContent = "Ожидание подключения";
    connectionState.textContent = "Отключено";
    serviceStatus.textContent = "Ожидание";
    sidebarStatus.textContent = "Готово к работе";
    topbarStatus.textContent = "Система в норме";
  }

  text.textContent = message;
}

function clearStreamCanvas() {
  if (!streamCanvas || !streamCtx) return;
  streamCtx.clearRect(0, 0, streamCanvas.width, streamCanvas.height);
  streamCanvas.width = 640;
  streamCanvas.height = 480;
  streamCtx.fillStyle = "#000";
  streamCtx.fillRect(0, 0, streamCanvas.width, streamCanvas.height);
}

function renderStreamFrame(data) {
  if (!streamCanvas || !streamCtx || !streamImage) return;

  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
  }

  const blob = new Blob([data], { type: "image/jpeg" });
  currentObjectUrl = URL.createObjectURL(blob);

  streamImage.onload = () => {
    streamCanvas.width = streamImage.width;
    streamCanvas.height = streamImage.height;
    streamCtx.clearRect(0, 0, streamCanvas.width, streamCanvas.height);
    streamCtx.drawImage(streamImage, 0, 0);
  };

  streamImage.src = currentObjectUrl;
}

function disconnectStream() {
  if (streamSocket) {
    streamSocket.close();
    streamSocket = null;
  }

  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = null;
  }

  if (streamImage) {
    streamImage.onload = null;
    streamImage.src = "";
  }

  clearStreamCanvas();
  setStreamStatus("Соединение разорвано.", false);
}

function connectStream() {
  const url = document.getElementById("streamUrl").value.trim() || "ws://localhost:8081/ws/processed";
  disconnectStream();

  setStreamStatus("Устанавливаем соединение...", false);

  try {
    streamSocket = new WebSocket(url);

    streamSocket.addEventListener("open", () => {
      setStreamStatus("Подключено к серверу трансляции.", true);
      frameCounter = 0;
      document.getElementById("frameCounter").textContent = "0";
    });

    streamSocket.addEventListener("message", (event) => {
      frameCounter += 1;
      document.getElementById("frameCounter").textContent = String(frameCounter);
      renderStreamFrame(event.data);
    });

    streamSocket.addEventListener("close", () => {
      setStreamStatus("Сервер закрыл соединение.", false);
    });

    streamSocket.addEventListener("error", () => {
      setStreamStatus("Не удалось подключиться к WebSocket-серверу. Проверьте адрес.", false);
    });
  } catch (error) {
    setStreamStatus("Некорректный URL WebSocket.", false);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  streamCanvas = document.getElementById("streamCanvas");
  streamCtx = streamCanvas?.getContext("2d");
  streamImage = new Image();

  renderAll();

  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });

  document.getElementById("employeeForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    state.employees.unshift({
      id: Date.now(),
      name: data.get("name"),
      position: data.get("position"),
      email: data.get("email"),
      phone: data.get("phone")
    });
    persistState();
    renderEmployees();
    event.currentTarget.reset();
  });

  document.getElementById("positionForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    state.positions.unshift({
      id: Date.now(),
      title: data.get("title"),
      department: data.get("department"),
      level: data.get("level")
    });
    persistState();
    renderPositions();
    event.currentTarget.reset();
  });

  document.getElementById("biometricForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    state.biometrics.unshift({
      id: Date.now(),
      name: data.get("name"),
      template: data.get("template"),
      status: data.get("status")
    });
    persistState();
    renderBiometrics();
    event.currentTarget.reset();
  });

  document.getElementById("connectStreamBtn").addEventListener("click", connectStream);
  document.getElementById("disconnectStreamBtn").addEventListener("click", disconnectStream);

  setStreamStatus("Ожидаем подключения к серверу.", false);
  document.getElementById("frameCounter").textContent = "0";
});