interface HeaderProps {
  healthStatus: string;
  userId: string;
  useLocalModel: boolean;
  onToggleLocalModel: (value: boolean) => void;
  onReset: () => void;
}

export default function Header({
  healthStatus,
  userId,
  useLocalModel,
  onToggleLocalModel,
  onReset,
}: HeaderProps) {
  return (
    <header className="app-header">
      <div>
        <h1>Companion Engine Demo</h1>
        <p>离线陪伴机器人对话引擎</p>
      </div>

      <div className="header-controls">
        <span className={`status-pill ${healthStatus === "ok" ? "ok" : "bad"}`}>
          后端：{healthStatus}
        </span>
        <span className="meta-pill">user_id：{userId}</span>
        <label className="toggle-row">
          <input
            type="checkbox"
            checked={useLocalModel}
            onChange={(event) => onToggleLocalModel(event.target.checked)}
          />
          本地模型
        </label>
        <button className="secondary-button" type="button" onClick={onReset}>
          重置用户
        </button>
      </div>
    </header>
  );
}
