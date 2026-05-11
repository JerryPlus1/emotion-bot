const memoryResult = document.querySelector("#memoryTestResult");
const proactiveResult = document.querySelector("#proactiveTestResult");
const memorySnapshot = document.querySelector("#labMemorySnapshot");
const userInput = document.querySelector("#labUserId");
const seedInput = document.querySelector("#labSeedMessage");
const recallInput = document.querySelector("#labRecallMessage");
const scenarioInput = document.querySelector("#labScenario");
const resetUserBtn = document.querySelector("#resetUserBtn");
const runMemoryTestBtn = document.querySelector("#runMemoryTestBtn");
const runProactiveTestBtn = document.querySelector("#runProactiveTestBtn");

resetUserBtn.addEventListener("click", resetUserData);
runMemoryTestBtn.addEventListener("click", runMemoryTest);
runProactiveTestBtn.addEventListener("click", runProactiveTest);

if (window.lucide) {
  window.lucide.createIcons();
}

refreshMemorySnapshot();

async function resetUserData() {
  const userId = currentUserId();
  if (!userId) return;
  resetUserBtn.disabled = true;
  try {
    await apiDelete(`/api/users/${encodeURIComponent(userId)}`);
    memoryResult.textContent = `已重置测试用户：${userId}`;
    proactiveResult.textContent = "尚未开始";
    await refreshMemorySnapshot();
  } catch (error) {
    memoryResult.textContent = `重置失败：${error.message}`;
  } finally {
    resetUserBtn.disabled = false;
  }
}

async function runMemoryTest() {
  const userId = currentUserId();
  const firstMessage = seedInput.value.trim();
  const recallMessage = recallInput.value.trim();

  if (!firstMessage || !recallMessage) {
    memoryResult.textContent = "请先填写写入消息和召回提问。";
    return;
  }

  runMemoryTestBtn.disabled = true;
  memoryResult.textContent = "正在执行记忆测试...";

  try {
    const first = await apiPost("/api/chat", {
      user_id: userId,
      message: firstMessage,
      use_memory: "always",
      history_weight: 0.7,
      memory_weight: 1.2,
      document_weight: 0.4,
    });

    const second = await apiPost("/api/chat", {
      user_id: userId,
      message: recallMessage,
      use_memory: "always",
      history_weight: 0.7,
      memory_weight: 1.2,
      document_weight: 0.4,
      conversation_id: first.conversation_id,
    });

    memoryResult.textContent = [
      `写入消息：${firstMessage}`,
      "",
      `召回提问：${recallMessage}`,
      `模型回复：${second.reply}`,
      `是否使用记忆：${second.used_memory ? "是" : "否"}`,
      `用户画像：${second.profile_summary || "暂无"}`,
      "",
      "命中的上下文：",
      ...(second.used_contexts || []).map(
        (item, index) => `${index + 1}. [${item.type}] ${item.content} (score=${item.score})`
      ),
    ].join("\n");

    await refreshMemorySnapshot();
  } catch (error) {
    memoryResult.textContent = `记忆测试失败：${error.message}`;
  } finally {
    runMemoryTestBtn.disabled = false;
  }
}

async function runProactiveTest() {
  const userId = currentUserId();
  runProactiveTestBtn.disabled = true;
  proactiveResult.textContent = "正在执行主动对话测试...";

  try {
    const scenario = scenarioInput.value.trim() || "工作";
    const data = await apiGet(
      `/api/proactive/check?user_id=${encodeURIComponent(userId)}&scenario=${encodeURIComponent(scenario)}&persist=false&force=true`
    );

    proactiveResult.textContent = [
      `测试用户：${userId}`,
      `场景：${scenario}`,
      `是否触发：${data.active ? "是" : "否"}`,
      `触发类型：${data.trigger || "无"}`,
      `关联话题：${data.topic || "无"}`,
      `主动消息：${data.message || "无"}`,
      "",
      "上下文：",
      ...((data.context || []).map(
        (item, index) => `${index + 1}. [${item.type}] ${item.content} (score=${item.score})`
      ) || ["无"]),
    ].join("\n");
  } catch (error) {
    proactiveResult.textContent = `主动对话测试失败：${error.message}`;
  } finally {
    runProactiveTestBtn.disabled = false;
  }
}

async function refreshMemorySnapshot() {
  const userId = currentUserId();
  if (!userId) {
    memorySnapshot.innerHTML = '<p class="empty">请输入测试用户。</p>';
    return;
  }

  const data = await apiGet(`/api/users/${encodeURIComponent(userId)}/memory`);
  const memories = data.memories || [];
  if (!memories.length) {
    memorySnapshot.innerHTML = '<p class="empty">当前用户还没有稳定记忆。</p>';
    return;
  }
  memorySnapshot.innerHTML = memories
    .slice(0, 10)
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

function currentUserId() {
  return userInput.value.trim() || "memory-lab-user";
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

async function apiDelete(path) {
  const response = await fetch(path, { method: "DELETE" });
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
