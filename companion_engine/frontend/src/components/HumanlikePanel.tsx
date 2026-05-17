import type { EngineOutput, UserState } from "../types";

interface HumanlikePanelProps {
  output: EngineOutput | null;
  state: UserState | null;
}

function Row({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="debug-field">
      <span>{label}</span>
      <strong>{value === undefined || value === null || value === "" ? "-" : String(value)}</strong>
    </div>
  );
}

export default function HumanlikePanel({ output, state }: HumanlikePanelProps) {
  const debug = output?.debug ?? {};

  return (
    <section className="panel humanlike-panel">
      <div className="panel-header">
        <h2>真人感处理</h2>
      </div>

      {!output ? (
        <p className="empty-text">发送消息后显示 raw/final 差异。</p>
      ) : (
        <>
          <div className="debug-grid">
            <Row label="humanlike" value={debug.humanlike_applied} />
            <Row label="silence" value={debug.used_silence} />
            <Row label="ask_question" value={debug.asked_question} />
            <Row label="recall_memory" value={debug.recalled_memory} />
            <Row label="emotion_trend" value={debug.emotion_trend} />
            <Row label="relationship" value={state?.relationship_state.relationship_stage} />
            <Row label="intimacy" value={state?.relationship_state.intimacy_level} />
          </div>
          <div className="compare-block">
            <h3>raw_reply</h3>
            <p>{String(debug.raw_reply ?? "-")}</p>
            <h3>final_reply</h3>
            <p>{String(debug.final_reply ?? output.response_text ?? "-")}</p>
          </div>
        </>
      )}
    </section>
  );
}
