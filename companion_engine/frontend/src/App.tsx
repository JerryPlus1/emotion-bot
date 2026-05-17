import { useCallback, useEffect, useState } from "react";
import { getHealth, getUserState, resetUser, savePersona, sendChat } from "./api/client";
import ChatPanel from "./components/ChatPanel";
import DebugPanel from "./components/DebugPanel";
import HardwarePanel from "./components/HardwarePanel";
import Header from "./components/Header";
import HumanlikePanel from "./components/HumanlikePanel";
import MemoryHitPanel from "./components/MemoryHitPanel";
import PersonaControls from "./components/PersonaControls";
import RepetitionPanel from "./components/RepetitionPanel";
import StatePanel from "./components/StatePanel";
import type { ChatMessage, EngineOutput, PersonaSnapshot, UserState } from "./types";

const USER_ID = "default_user";

export default function App() {
  const [healthStatus, setHealthStatus] = useState("checking");
  const [useLocalModel, setUseLocalModel] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastOutput, setLastOutput] = useState<EngineOutput | null>(null);
  const [userState, setUserState] = useState<UserState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  const refreshState = useCallback(async () => {
    // 状态面板从后端读取真实持久化状态。
    const state = await getUserState(USER_ID);
    setUserState(state);
  }, []);

  useEffect(() => {
    async function boot() {
      try {
        const health = await getHealth();
        setHealthStatus(health.status);
        await refreshState();
      } catch (err) {
        setHealthStatus("offline");
        setError(err instanceof Error ? err.message : "后端连接失败");
      }
    }

    void boot();
  }, [refreshState]);

  async function handleSend(text: string) {
    if (!text.trim()) {
      return;
    }

    setError(null);
    setIsSending(true);
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };
    setMessages((current) => [...current, userMessage]);

    try {
      const output = await sendChat(
        {
          user_id: USER_ID,
          event_type: "user_direct_chat",
          user_text: text,
          scene: {
            time: new Date().toTimeString().slice(0, 5),
            location: "web_demo",
            activity: "chat",
            is_user_nearby: true,
          },
        },
        useLocalModel,
      );

      setLastOutput(output);
      const assistantText = output.should_speak
        ? output.response_text || "机器人暂时没有生成回复。"
        : "机器人选择暂时不打扰";
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: output.should_speak ? "assistant" : "system",
          content: assistantText,
        },
      ]);
      await refreshState();
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送失败");
    } finally {
      setIsSending(false);
    }
  }

  async function handleReset() {
    setError(null);

    try {
      await resetUser(USER_ID);
      setMessages([]);
      setLastOutput(null);
      await refreshState();
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置失败");
    }
  }

  async function handlePersonaSave(persona: PersonaSnapshot) {
    setError(null);

    try {
      await savePersona(USER_ID, persona);
      await refreshState();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存 Persona 失败");
    }
  }

  return (
    <div className="app-shell">
      <Header
        healthStatus={healthStatus}
        userId={USER_ID}
        useLocalModel={useLocalModel}
        onToggleLocalModel={setUseLocalModel}
        onReset={handleReset}
      />

      {error && <div className="error-banner">{error}</div>}

      <main className="dashboard-grid">
        <ChatPanel messages={messages} isSending={isSending} onSend={handleSend} />
        <HumanlikePanel output={lastOutput} state={userState} />
        <DebugPanel output={lastOutput} />
        <MemoryHitPanel output={lastOutput} />
        <RepetitionPanel output={lastOutput} messages={messages} />
        <PersonaControls persona={userState?.persona ?? null} onSave={handlePersonaSave} />
        <StatePanel state={userState} />
        <HardwarePanel actions={lastOutput?.hardware_actions ?? null} />
      </main>
    </div>
  );
}
