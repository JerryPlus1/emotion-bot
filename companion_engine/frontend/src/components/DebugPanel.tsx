import type { EngineOutput } from "../types";

interface DebugPanelProps {
  output: EngineOutput | null;
}

function Field({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="debug-field">
      <span>{label}</span>
      <strong>{value === null || value === undefined || value === "" ? "-" : String(value)}</strong>
    </div>
  );
}

export default function DebugPanel({ output }: DebugPanelProps) {
  return (
    <section className="panel debug-panel">
      <div className="panel-header">
        <h2>调试输出</h2>
      </div>

      {!output ? (
        <p className="empty-text">发送消息后显示最近一次 EngineOutput。</p>
      ) : (
        <>
          <div className="debug-grid">
            <Field label="intent" value={output.detected_intent} />
            <Field label="emotion" value={output.detected_emotion} />
            <Field label="risk" value={output.risk_level} />
            <Field label="strategy" value={output.strategy} />
            <Field label="proactive" value={output.proactive_type} />
            <Field label="question" value={output.question_type} />
            <Field label="should_speak" value={output.should_speak} />
            <Field label="reason" value={output.debug?.speak_reason} />
          </div>
          <pre className="json-block">{JSON.stringify(output.debug, null, 2)}</pre>
        </>
      )}
    </section>
  );
}
