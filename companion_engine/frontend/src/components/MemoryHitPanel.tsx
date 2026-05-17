import type { EngineOutput } from "../types";

interface MemoryHitPanelProps {
  output: EngineOutput | null;
}

function extractMemoryReference(finalReply: string, recalled: boolean): string {
  // 以当前后端的自然记忆引用开头做轻量识别，避免前端理解复杂业务。
  if (!recalled) {
    return "-";
  }

  const markers = ["之前你提过类似的感觉", "我想到你之前也有过这种时候", "我一下子想到你上次那种状态"];
  const marker = markers.find((item) => finalReply.includes(item));
  return marker ?? "自然提起了一条记忆";
}

export default function MemoryHitPanel({ output }: MemoryHitPanelProps) {
  const debug = output?.debug ?? {};
  const recalled = Boolean(debug.recalled_memory);
  const finalReply = String(debug.final_reply ?? output?.response_text ?? "");

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>记忆命中</h2>
      </div>

      {!output ? (
        <p className="empty-text">暂无记忆引用信息。</p>
      ) : (
        <div className="state-stack">
          <div className="debug-field">
            <span>本轮是否使用记忆</span>
            <strong>{String(recalled)}</strong>
          </div>
          <div className="debug-field">
            <span>使用了哪条记忆</span>
            <strong>{recalled ? finalReply : "-"}</strong>
          </div>
          <div className="debug-field">
            <span>记忆引用方式</span>
            <strong>{extractMemoryReference(finalReply, recalled)}</strong>
          </div>
        </div>
      )}
    </section>
  );
}
