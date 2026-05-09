const state = {
  conversationId: null,
  lastProactiveKey: "",
  sending: false,
};

const el = {
  healthText: document.querySelector("#healthText"),
  userId: document.querySelector("#userId"),
  refreshMemoryBtn: document.querySelector("#refreshMemoryBtn"),
  memoryMode: document.querySelector("#memoryMode"),
  memoryWeight: document.querySelector("#memoryWeight"),
  memoryWeightValue: document.querySelector("#memoryWeightValue"),
  historyWeight: document.querySelector("#historyWeight"),
  historyWeightValue: document.querySelector("#historyWeightValue"),
  documentWeight: document.querySelector("#documentWeight"),
  documentWeightValue: document.querySelector("#documentWeightValue"),
  scenarioInput: document.querySelector("#scenarioInput"),
  ttsToggle: document.querySelector("#ttsToggle"),
  proactiveBtn: document.querySelector("#proactiveBtn"),
  startTalkBtn: document.querySelector("#startTalkBtn"),
  proactiveBanner: document.querySelector("#proactiveBanner"),
  sessionMeta: document.querySelector("#sessionMeta"),
  messages: document.querySelector("#messages"),
  chatForm: document.querySelector("#chatForm"),
  messageInput: document.querySelector("#messageInput"),
  sendBtn: document.querySelector("#sendBtn"),
  clearBtn: document.querySelector("#clearBtn"),
  profileSummary: document.querySelector("#profileSummary"),
  contextList: document.querySelector("#contextList"),
  docTitle: document.querySelector("#docTitle"),
  docContent: document.querySelector("#docContent"),
  ingestBtn: document.querySelector("#ingestBtn"),
  memoryList: document.querySelector("#memoryList"),
};

function init() {
  el.userId.value = localStorage.getItem("emotion-bot-user-id") || "default";
  el.ttsToggle.checked = localStorage.getItem("emotion-bot-tts") === "true";
  bindEvents();
  updateSliderLabels();
  renderWelcome();
  refreshHealth();
  loadMemory();
  setInterval(checkProactive, 45000);
  createIcons();
}

function bindEvents() {
  [el.memoryWeight, el.historyWeight, el.documentWeight].forEach((input) => {
    input.addEventListener("input", updateSliderLabels);
  });

  el.userId.addEventListener("change", () => {
    localStorage.setItem("emotion-bot-user-id", currentUserId());
    state.conversationId = null;
    loadMemory();
  });

  el.ttsToggle.addEventListener("change", () => {
    localStorage.setItem("emotion-bot-tts", String(el.ttsToggle.checked));
  });

  el.refreshMemoryBtn.addEventListener("click", loadMemory);
  el.proactiveBtn.addEventListener("click", () => checkProactive(true, false));
  el.startTalkBtn.addEventListener("click", startProactiveConversation);
  el.clearBtn.addEventListener("click", () => {
    el.messages.innerHTML = "";
    renderWelcome();
  });
  el.ingestBtn.addEventListener("click", ingestDocument);
  el.chatForm.addEventListener("submit", sendMessage);
  el.messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      el.chatForm.requestSubmit();
    }
  });
}

function currentUserId() {
  return el.userId.value.trim() || "default";
}

function updateSliderLabels() {
  el.memoryWeightValue.textContent = Number(el.memoryWeight.value).toFixed(2);
  el.historyWeightValue.textContent = Number(el.historyWeight.value).toFixed(2);
  el.documentWeightValue.textContent = Number(el.documentWeight.value).toFixed(2);
}

function renderWelcome() {
  appendMessage(
    "assistant",
    "你好，我已经准备好记住重要内容，也会在合适的时候主动开口。你可以直接开始聊。",
    "本地会话"
  );
}

async function refreshHealth() {
  try {
    const data = await apiGet("/api/health");
    if (data.effective_backend === "llama-cpp-gguf" && data.model_exists) {
      el.healthText.textContent = "离线 GGUF 模型就绪";
    } else if (data.effective_backend === "mock") {
      el.healthText.textContent = "mock 调试模式";
    } else {
      el.healthText.textContent = data.model_exists ? "本地模型已找到" : "未找到本地模型";
    }
  } catch (error) {
    el.healthText.textContent = "服务未连接";
  }
}

async function sendMessage(event) {
  event.preventDefault();
  if (state.sending) return;

  const message = el.messageInput.value.trim();
  if (!message) return;

  state.sending = true;
  el.sendBtn.disabled = true;
  appendMessage("user", message, currentUserId());
  el.messageInput.value = "";
  appendTyping();

  try {
    const payload = {
      user_id: currentUserId(),
      message,
      conversation_id: state.conversationId,
      use_memory: el.memoryMode.value,
      memory_weight: Number(el.memoryWeight.value),
      history_weight: Number(el.historyWeight.value),
      document_weight: Number(el.documentWeight.value),
      scenario: el.scenarioInput.value.trim() || null,
    };
    const data = await apiPost("/api/chat", payload);
    state.conversationId = data.conversation_id;
    removeTyping();
    appendMessage("assistant", data.reply, data.used_memory ? "使用了相关上下文" : "未使用历史上下文");
    renderContexts(data.used_contexts || []);
    renderProfile(data.profile_summary || "");
    el.sessionMeta.textContent = data.used_memory ? "已结合相关记忆" : "本轮未结合历史";
    if (data.proactive_hint) {
      showProactive(data.proactive_hint, false);
    }
    if (el.ttsToggle.checked) {
      speak(data.reply);
    }
    loadMemory();
  } catch (error) {
    removeTyping();
    appendMessage("assistant", `请求失败：${error.message}`, "错误");
  } finally {
    state.sending = false;
    el.sendBtn.disabled = false;
    el.messageInput.focus();
  }
}

function appendTyping() {
  const node = document.createElement("article");
  node.className = "message assistant typing";
  node.innerHTML = '<div class="meta-row">Emotion Bot</div><div class="bubble">正在思考...</div>';
  el.messages.appendChild(node);
  scrollMessages();
}

function removeTyping() {
  const typing = el.messages.querySelector(".typing");
  if (typing) typing.remove();
}

function appendMessage(role, content, meta) {
  const node = document.createElement("article");
  node.className = `message ${role}`;
  const safeContent = escapeHtml(content);
  const canSpeak = role === "assistant";
  node.innerHTML = `
    <div class="meta-row">
      <span>${escapeHtml(meta || (role === "user" ? "你" : "Emotion Bot"))}</span>
      ${
        canSpeak
          ? '<button class="speak-button" type="button" title="朗读"><i data-lucide="volume-2"></i></button>'
          : ""
      }
    </div>
    <div class="bubble">${safeContent}</div>
  `;
  if (canSpeak) {
    node.querySelector(".speak-button").addEventListener("click", () => speak(content));
  }
  el.messages.appendChild(node);
  createIcons();
  scrollMessages();
}

function scrollMessages() {
  el.messages.scrollTop = el.messages.scrollHeight;
}

async function loadMemory() {
  try {
    const data = await apiGet(`/api/users/${encodeURIComponent(currentUserId())}/memory`);
    renderProfile(data.profile_summary || "");
    renderMemories(data.memories || []);
  } catch (error) {
    renderProfile("");
    el.memoryList.innerHTML = `<p class="empty">记忆读取失败：${escapeHtml(error.message)}</p>`;
  }
}

function renderProfile(summary) {
  el.profileSummary.textContent = summary || "暂无画像";
}

function renderMemories(memories) {
  if (!memories.length) {
    el.memoryList.innerHTML = '<p class="empty">暂无长期记忆</p>';
    return;
  }
  el.memoryList.innerHTML = memories
    .map(
      (item) => `
        <div class="memory-item">
          <div class="tag-row">
            <span class="tag memory">${escapeHtml(item.kind)}</span>
            <span class="tag">权重 ${Number(item.weight).toFixed(2)}</span>
          </div>
          <div>${escapeHtml(item.content)}</div>
        </div>
      `
    )
    .join("");
}

function renderContexts(contexts) {
  if (!contexts.length) {
    el.contextList.innerHTML = '<p class="empty">本轮没有使用上下文</p>';
    return;
  }
  el.contextList.innerHTML = contexts
    .map((item) => {
      const typeClass = item.type === "memory" ? "memory" : item.type === "history" ? "history" : "document";
      return `
        <div class="context-item">
          <div class="tag-row">
            <span class="tag ${typeClass}">${escapeHtml(item.type)}</span>
            <span class="tag">相关度 ${Number(item.score).toFixed(3)}</span>
          </div>
          <div>${escapeHtml(item.content)}</div>
        </div>
      `;
    })
    .join("");
}

async function ingestDocument() {
  const title = el.docTitle.value.trim();
  const content = el.docContent.value.trim();
  if (!title || !content) {
    appendMessage("assistant", "知识库需要标题和正文。", "系统");
    return;
  }
  el.ingestBtn.disabled = true;
  try {
    const data = await apiPost("/api/documents", {
      title,
      content,
      source: "web-ui",
      user_id: currentUserId(),
      weight: Number(el.documentWeight.value),
    });
    appendMessage("assistant", `已写入知识库，分片 ${data.chunks} 个。`, "系统");
    el.docTitle.value = "";
    el.docContent.value = "";
  } catch (error) {
    appendMessage("assistant", `知识库写入失败：${error.message}`, "错误");
  } finally {
    el.ingestBtn.disabled = false;
  }
}

async function checkProactive(manual = false, force = false, appendToChat = true) {
  try {
    const params = new URLSearchParams({
      user_id: currentUserId(),
      persist: "true",
      force: force ? "true" : "false",
    });
    const scenario = el.scenarioInput.value.trim();
    if (scenario) params.set("scenario", scenario);
    const data = await apiGet(`/api/proactive/check?${params.toString()}`);
    if (data.active) {
      showProactive(data, appendToChat);
      return data;
    } else if (manual) {
      showProactive(
        {
          trigger: "manual",
          topic: "当前状态",
          message: "现在没有新的主动触发，但我在。你想聊什么都可以。",
        },
        false
      );
    }
    return data;
  } catch (error) {
    if (manual) {
      showProactive({ trigger: "error", topic: "连接", message: `主动检查失败：${error.message}` }, false);
    }
    throw error;
  }
}

async function startProactiveConversation() {
  if (state.sending) return;
  el.startTalkBtn.disabled = true;
  try {
    const data = await checkProactive(false, true, false);
    if (data && data.active && data.message) {
      appendMessage("assistant", data.message, `主动对话：${data.trigger}`);
      if (el.ttsToggle.checked) {
        speak(data.message);
      }
    }
  } catch (error) {
    appendMessage("assistant", `主动对话失败：${error.message}`, "错误");
  } finally {
    el.startTalkBtn.disabled = false;
  }
}

function showProactive(data, appendToChat) {
  const key = `${data.trigger}:${data.message}`;
  if (key === state.lastProactiveKey && appendToChat) return;
  state.lastProactiveKey = key;
  el.proactiveBanner.classList.remove("hidden");
  el.proactiveBanner.innerHTML = `
    <strong>${escapeHtml(data.trigger || "主动提示")}</strong>
    <div>${escapeHtml(data.message || "")}</div>
  `;
  if (appendToChat) {
    appendMessage("assistant", data.message, `主动对话：${data.trigger}`);
    if (el.ttsToggle.checked) {
      speak(data.message);
    }
  }
}

function speak(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "zh-CN";
  utterance.rate = 1;
  utterance.pitch = 1;
  const voices = window.speechSynthesis.getVoices();
  const zhVoice = voices.find((voice) => voice.lang.toLowerCase().startsWith("zh"));
  if (zhVoice) utterance.voice = zhVoice;
  window.speechSynthesis.speak(utterance);
}

async function apiGet(path) {
  const response = await fetch(path);
  return parseResponse(response);
}

async function apiPost(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

async function parseResponse(response) {
  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch (error) {
    data = { detail: text };
  }
  if (!response.ok) {
    const detail = data.detail || data.message || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function createIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

init();
