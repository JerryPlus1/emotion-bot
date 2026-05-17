export interface SceneContext {
  time?: string | null;
  location?: string | null;
  activity?: string | null;
  is_user_nearby: boolean;
}

export interface EngineInput {
  user_id: string;
  event_type: string;
  user_text?: string | null;
  scene: SceneContext;
}

export interface HardwareActions {
  expression: string;
  light_color: string;
  motion: string;
  speech_text?: string | null;
}

export interface EngineOutput {
  should_speak: boolean;
  response_text?: string | null;
  detected_intent?: string | null;
  detected_emotion?: string | null;
  risk_level: string;
  strategy?: string | null;
  proactive_type?: string | null;
  question_type?: string | null;
  memory_updates: unknown[];
  persona_updates: unknown[];
  hardware_actions?: HardwareActions | null;
  debug: Record<string, unknown>;
}

export interface UserProfile {
  user_id: string;
  preferred_address?: string | null;
  preferred_support_style: string;
  initiative_tolerance: string;
  disliked_responses: string[];
  liked_topics: string[];
  avoided_topics: string[];
  last_known_mood?: string | null;
}

export interface PersonaSnapshot {
  role_style: string;
  warmth_level: string;
  initiative_level: string;
  analysis_level: string;
  playfulness_level: string;
  speech_length: string;
  companionship_style: string;
}

export interface RelationshipState {
  user_id: string;
  relationship_stage: string;
  trust_level: number;
  intimacy_level: number;
  user_openness: number;
  recent_interaction_quality: string;
  last_meaningful_topic?: string | null;
}

export interface LongTermMemory {
  memory_type: string;
  content: string;
  importance: number;
  emotional_valence: string;
  source_text: string;
}

export interface UserState {
  user_profile: UserProfile;
  persona: PersonaSnapshot;
  relationship_state: RelationshipState;
  recent_memories: LongTermMemory[];
  important_memories: LongTermMemory[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}
