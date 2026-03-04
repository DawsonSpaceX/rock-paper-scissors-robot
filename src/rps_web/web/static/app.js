const phase = document.getElementById("phase");
const selection = document.getElementById("selection");
const computer = document.getElementById("computer");
const result = document.getElementById("result");
const you = document.getElementById("you");
const cpu = document.getElementById("cpu");
const ties = document.getElementById("ties");
const cameraStatus = document.getElementById("camera-status");

const protocol = location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${protocol}://${location.host}/ws`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  phase.textContent = data.phase;
  selection.textContent = data.selection;
  computer.textContent = data.computer ?? "-";
  result.textContent = data.result ?? "-";
  you.textContent = data.score.you;
  cpu.textContent = data.score.cpu;
  ties.textContent = data.score.ties;

  if (!data.camera_available) {
    cameraStatus.classList.remove("hidden");
  } else {
    cameraStatus.classList.add("hidden");
  }
};

ws.onclose = () => {
  phase.textContent = "disconnected";
};
