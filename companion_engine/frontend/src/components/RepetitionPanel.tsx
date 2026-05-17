import type { ChatMessage, EngineOutput } from "../types";

interface RepetitionPanelProps {
  output: EngineOutput | null;
  messages: ChatMessage[];
}

export default function RepetitionPanel({ output, messages }: RepetitionPanelProps) {
  const recentBotMessages = messages
    .filter((message) => message.role === "assistant")
    .slice(-3)
    .map((message) => message.content);
  const rawReply = String(output?.debug?.raw_reply ?? "");
  const finalReply = String(output?.debug?.final_reply ?? output?.response_text ?? "");
  const triggered = Boolean(output && rawReply && finalReply && rawReply !== finalReply);

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>重复控制</h2>
      </div>

      <div className="state-stack">
        <div className="debug-field">
          <span>是否触发重复/风格控制</span>
          <strong>{String(triggered)}</strong>
        </div>
        <section className="state-section">
          <h3>最近机器人回复</h3>
          <pre className="json-block compact">{JSON.stringify(recentBotMessages, null, 2)}</pre>
        </section>
      </div>
    </section>
  );
}
