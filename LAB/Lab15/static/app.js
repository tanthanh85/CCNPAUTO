const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const questionInput = document.querySelector("#question");
const summary = document.querySelector("#summary");

function addMessage(role, text) {
  const row = document.createElement("div");
  row.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

async function loadSummary() {
  try {
    const response = await fetch("/api/summary");
    const data = await response.json();
    summary.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    summary.textContent = `Unable to load summary: ${error}`;
  }
}

async function ask(question) {
  addMessage("user", question);
  addMessage("assistant", "Calling the MCP route tool and asking the local model...");

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({question}),
  });
  const data = await response.json();

  messages.lastElementChild.remove();
  if (data.ok) {
    addMessage("assistant", data.answer);
    summary.textContent = JSON.stringify(data.context, null, 2);
  } else {
    addMessage("assistant", `Error: ${data.error}`);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) {
    return;
  }
  questionInput.value = "";
  await ask(question);
});

document.querySelectorAll(".prompt").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.textContent;
    questionInput.focus();
  });
});

loadSummary();
