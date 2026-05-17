import type { HardwareActions } from "../types";

interface HardwarePanelProps {
  actions: HardwareActions | null;
}

export default function HardwarePanel({ actions }: HardwarePanelProps) {
  return (
    <section className="panel hardware-panel">
      <div className="panel-header">
        <h2>硬件动作预览</h2>
      </div>

      {!actions ? (
        <p className="empty-text">暂无硬件动作。</p>
      ) : (
        <div className="hardware-grid">
          <div>
            <span>expression</span>
            <strong>{actions.expression}</strong>
          </div>
          <div>
            <span>light_color</span>
            <strong>{actions.light_color}</strong>
          </div>
          <div>
            <span>motion</span>
            <strong>{actions.motion}</strong>
          </div>
          <div className="hardware-speech">
            <span>speech_text</span>
            <p>{actions.speech_text || "-"}</p>
          </div>
        </div>
      )}
    </section>
  );
}
