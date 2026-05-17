import type { UserState } from "../types";

interface StatePanelProps {
  state: UserState | null;
}

function JsonSection({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="state-section">
      <h3>{title}</h3>
      <pre className="json-block compact">{JSON.stringify(value, null, 2)}</pre>
    </section>
  );
}

export default function StatePanel({ state }: StatePanelProps) {
  return (
    <section className="panel state-panel">
      <div className="panel-header">
        <h2>用户状态</h2>
      </div>

      {!state ? (
        <p className="empty-text">正在读取状态。</p>
      ) : (
        <div className="state-stack">
          <JsonSection title="UserProfile" value={state.user_profile} />
          <JsonSection title="PersonaSnapshot" value={state.persona} />
          <JsonSection title="RelationshipState" value={state.relationship_state} />
          <JsonSection title="Recent Memories" value={state.recent_memories} />
          <JsonSection title="Important Memories" value={state.important_memories} />
        </div>
      )}
    </section>
  );
}
