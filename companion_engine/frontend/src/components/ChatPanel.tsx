import { FormEvent, KeyboardEvent, useState } from "react";
import type { ChatMessage } from "../types";

interface ChatPanelProps {
  messages: ChatMessage[];
  isSending: boolean;
  onSend: (text: string) => Promise<void>;
}

export default function ChatPanel({ messages, isSending, onSend }: ChatPanelProps) {
  const [draft, setDraft] = useState("");

  async function submit() {
    const text = draft.trim();
    if (!text || isSending) {
      return;
    }

    setDraft("");
    await onSend(text);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void submit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter 发送，Shift+Enter 保留换行。
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <h2>对话</h2>
      </div>

      <div className="message-list">
        {messages.length === 0 && <p className="empty-text">开始说点什么吧。</p>}
        {messages.map((message) => (
          <div key={message.id} className={`message-row ${message.role}`}>
            <div className="message-bubble">{message.content}</div>
          </div>
        ))}
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入一句话，按 Enter 发送"
          rows={3}
        />
        <button className="primary-button" type="submit" disabled={isSending}>
          {isSending ? "发送中" : "发送"}
        </button>
      </form>
    </section>
  );
}
