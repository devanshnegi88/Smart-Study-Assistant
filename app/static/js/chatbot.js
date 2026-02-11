const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");

function addMessage(text, sender) {
  const messageElement = document.createElement("div");
  messageElement.classList.add("message", sender === "user" ? "user-message" : "bot-message");

  // Convert code blocks ```c ... ```
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  text = text.replace(codeBlockRegex, (match, lang, code) => {
    return `<pre class="code-block"><code>${code}</code></pre>`;
  });

  // Convert inline code `code`
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Convert **bold**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Numbered lists
  text = text.replace(/^(\d+)\.\s+(.*)$/gm, '<li>$2</li>');
  if (text.includes('<li>') && !text.includes('<ol>')) text = '<ol class="explanation">' + text + '</ol>';

  // Bullet lists
  text = text.replace(/^\*\s+(.*)$/gm, '<li>$1</li>');
  if (text.includes('<li>') && !text.includes('<ul>') && !text.includes('<ol>')) {
    text = '<ul class="explanation">' + text + '</ul>';
  }

  // Wrap plain text in explanation if no list/code
  if (!text.includes('<ul>') && !text.includes('<ol>') && !text.includes('class="code-block"')) {
    text = `<div class="explanation">${text}</div>`;
  }

  messageElement.innerHTML = text;

  // Add timestamp
  const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  const timestamp = document.createElement("span");
  timestamp.classList.add("message-time");
  timestamp.textContent = time;
  messageElement.appendChild(timestamp);

  chatBox.appendChild(messageElement);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Typing indicator
function createTypingIndicator() {
  const typingElement = document.createElement("div");
  typingElement.classList.add("message", "bot-message");
  typingElement.id = "typing-indicator";

  for (let i = 0; i < 3; i++) {
    const dot = document.createElement("span");
    dot.classList.add("typing");
    typingElement.appendChild(dot);
  }

  chatBox.appendChild(typingElement);
  chatBox.scrollTop = chatBox.scrollHeight;
  return typingElement;
}

async function getGeminiResponse(prompt) {
  try {
    const response = await fetch("/chatbot/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: prompt })
    });

    const data = await response.json();
    if (data.response) return data.response;
    if (data.error) return "❌ " + data.error;
    return "⚠️ No response from Gemini.";
  } catch (error) {
    console.error("Error:", error);
    return "⚠️ Connection error with backend.";
  }
}

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  addMessage(message, "user");
  userInput.value = "";

  const typingIndicator = createTypingIndicator();
  const reply = await getGeminiResponse(message);
  typingIndicator.remove();
  addMessage(reply, "bot");
}

userInput.addEventListener("keypress", function (e) {
  if (e.key === "Enter") sendMessage();
});

function slidbar() {
  document.body.classList.toggle("open");
}
