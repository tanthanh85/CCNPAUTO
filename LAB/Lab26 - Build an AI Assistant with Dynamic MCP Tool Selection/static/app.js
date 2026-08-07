const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const question = document.querySelector("#question");
const trace = document.querySelector("#trace");
const tools = document.querySelector("#tools");

function addMessage(role, text) {
  const row = document.createElement("div");
  row.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
  return row;
}

async function discoverTools() {
  try {
    const response = await fetch("/api/tools");
    const data = await response.json();
    if (!data.ok) throw new Error(data.error);
    tools.innerHTML = "";
    data.tools.forEach((entry) => {
      const card = document.createElement("article");
      card.className = "tool-card";
      const name = document.createElement("strong");
      name.textContent = entry.function.name;
      const description = document.createElement("p");
      description.textContent = entry.function.description;
      card.append(name, description);
      tools.appendChild(card);
    });
  } catch (error) {
    tools.textContent = `Discovery failed: ${error}`;
  }
}

async function ask(text) {
  addMessage("user", text);
  const pending = addMessage("assistant", "The model is selecting tools and the orchestrator is validating them...");
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: text}),
    });
    const data = await response.json();
    pending.remove();
    if (!data.ok) {
      addMessage("assistant", `Error: ${data.error}`);
      return;
    }
    addMessage(
      "assistant",
      `${data.provider} · ${data.model} · ${data.elapsed_ms} ms · ${data.iterations} iteration(s)\n\n${data.answer}`,
    );
    trace.textContent = JSON.stringify(data.tool_trace, null, 2);
  } catch (error) {
    pending.remove();
    addMessage("assistant", `Request failed: ${error}`);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = question.value.trim();
  if (!text) return;
  question.value = "";
  await ask(text);
});

document.querySelectorAll(".prompts button").forEach((button) => {
  button.addEventListener("click", () => {
    question.value = button.textContent;
    question.focus();
  });
});

discoverTools();
