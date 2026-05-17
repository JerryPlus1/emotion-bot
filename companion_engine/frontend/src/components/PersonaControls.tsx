import { FormEvent, useEffect, useState } from "react";
import type { PersonaSnapshot } from "../types";

interface PersonaControlsProps {
  persona: PersonaSnapshot | null;
  onSave: (persona: PersonaSnapshot) => Promise<void>;
}

const OPTIONS = {
  warmth_level: ["low", "medium", "high"],
  analysis_level: ["low", "medium", "high"],
  playfulness_level: ["low", "medium", "high"],
  speech_length: ["short", "medium", "long"],
  companionship_style: ["listen_first", "comfort_first", "advice_first"],
};

export default function PersonaControls({ persona, onSave }: PersonaControlsProps) {
  const [draft, setDraft] = useState<PersonaSnapshot | null>(persona);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setDraft(persona);
  }, [persona]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!draft || saving) {
      return;
    }

    setSaving(true);
    try {
      await onSave(draft);
    } finally {
      setSaving(false);
    }
  }

  function updateField<K extends keyof PersonaSnapshot>(key: K, value: PersonaSnapshot[K]) {
    setDraft((current) => (current ? { ...current, [key]: value } : current));
  }

  if (!draft) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2>Persona 调节</h2>
        </div>
        <p className="empty-text">正在读取 Persona。</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Persona 调节</h2>
      </div>

      <form className="persona-form" onSubmit={handleSubmit}>
        {Object.entries(OPTIONS).map(([key, values]) => (
          <label key={key}>
            <span>{key}</span>
            <select
              value={draft[key as keyof PersonaSnapshot]}
              onChange={(event) =>
                updateField(key as keyof PersonaSnapshot, event.target.value as never)
              }
            >
              {values.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        ))}
        <button className="secondary-button" type="submit" disabled={saving}>
          {saving ? "保存中" : "保存 Persona"}
        </button>
      </form>
    </section>
  );
}
