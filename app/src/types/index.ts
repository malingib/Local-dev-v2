// TypeScript types matching the backend Pydantic models

export const SessionState = {
  INGEST: "ingest",
  AUDIT: "audit",
  HYPOTHESIS_LOOP: "hypothesis_loop",
  APPROVAL_FLOW: "approval_flow",
  APPLY: "apply",
  COMPLETE: "complete",
  ESCALATED: "escalated",
  ABANDONED: "abandoned",
} as const
export type SessionState = typeof SessionState[keyof typeof SessionState]

export const SessionMode = {
  AUDIT: "audit",
  AUDIT_FIX: "audit_fix",
  GOAL: "goal",
} as const
export type SessionMode = typeof SessionMode[keyof typeof SessionMode]

export const FindingStatus = {
  OPEN: "open",
  IN_PROGRESS: "in_progress",
  AWAITING_APPROVAL: "awaiting_approval",
  APPROVED: "approved",
  REJECTED: "rejected",
  APPLIED: "applied",
  ESCALATED: "escalated",
} as const
export type FindingStatus = typeof FindingStatus[keyof typeof FindingStatus]

export const Severity = {
  CRITICAL: "critical",
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
  INFO: "info",
} as const
export type Severity = typeof Severity[keyof typeof Severity]

export const AgentType = {
  AUDITOR: "auditor",
  UI: "ui",
  SECURITY: "security",
  PERFORMANCE: "performance",
  MOBILE: "mobile",
  META: "meta",
} as const
export type AgentType = typeof AgentType[keyof typeof AgentType]

export const FindingType = {
  BUG: "bug",
  SECURITY: "security",
  PERFORMANCE: "performance",
  UI: "ui",
  ACCESSIBILITY: "accessibility",
  CODE_QUALITY: "code_quality",
  BEST_PRACTICE: "best_practice",
  DEPRECATED: "deprecated",
} as const
export type FindingType = typeof FindingType[keyof typeof FindingType]

export const ApprovalStage = {
  SKETCH: "sketch",
  PREVIEW: "preview",
  FULL: "full",
} as const
export type ApprovalStage = typeof ApprovalStage[keyof typeof ApprovalStage]

export interface Hypothesis {
  id: string
  claim: string
  confidence: number
  status: string
  evidence_for: string[]
  evidence_against: string[]
  created_at: string
}

export interface Experiment {
  id: string
  hypothesis_id: string
  action: string
  tool: string
  params: Record<string, unknown>
  result: string
  information_gain: number
  created_at: string
}

export interface PatchChange {
  file: string
  find: string
  replace: string
}

export interface Finding {
  id: string
  title: string
  description: string
  type: FindingType
  severity: Severity
  status: FindingStatus
  agent: AgentType
  location: Record<string, unknown>
  code_snippet: string
  suggested_fix: string
  proposed_patch: string
  patch_explanation: string
  hypothesis_tree: Hypothesis[]
  experiments: Experiment[]
  rejection_reason: string
  auto_approvable: boolean
  approval_stage?: ApprovalStage
  created_at: string
  updated_at: string
}

export interface ProjectInfo {
  name: string
  path: string
  github_url?: string
  detected_stack: string[]
  routes: string[]
  dependencies: Record<string, string>
}

export interface ActivityLog {
  id: string
  agent: string
  message: string
  level: "info" | "success" | "warning" | "error"
  timestamp: string
  metadata: Record<string, unknown>
}

export interface RejectionMemory {
  finding_title: string
  finding_type: string
  location: Record<string, unknown>
  reason: string
  timestamp: string
}

export interface Session {
  id: string
  mode: SessionMode
  state: SessionState
  goal: string
  project?: ProjectInfo
  findings: Finding[]
  approval_queue: string[]
  current_finding_id?: string
  activity_log: ActivityLog[]
  rejection_memory: RejectionMemory[]
  stack_detected: boolean
  created_at: string
  updated_at: string
  completed_at?: string
  metadata: Record<string, unknown>
}

export interface SessionSummary {
  id: string
  state: string
  mode: string
  project_name: string
  project_path: string
  findings_total: number
  findings_critical: number
  findings_high: number
  findings_open: number
  findings_applied: number
  approval_queue_size: number
  created_at: string
  updated_at: string
}

export interface Config {
  project_name: string
  github_url?: string
  local_path?: string
  enabled_agents: string[]
  has_google_key: boolean
  has_groq_key: boolean
  has_github_token: boolean
  has_figma_token: boolean
}

export interface HealthCheck {
  status: string
  has_google_key: boolean
  has_groq_key: boolean
  has_openrouter_key: boolean
  has_github_token: boolean
  version: string
}

// ─── Soul ──────────────────────────────────────────────────────────────────────

export interface SoulTemplate {
  id: string
  name: string
  description: string
  category: string
}

export interface SoulState {
  soul: string
  user: string
  agents: string
  habits: string
  mistakes: string
}

export type SoulFileType = "soul" | "user" | "agents" | "habits" | "mistakes"

export interface SoulTemplate {
  id: string
  name: string
  description: string
  traits: string[]
  system_prompt_additions: string
  soul_content: string
  user_content: string
  agents_content: string
  created_at: string
  updated_at: string
}

// ─── Skills ────────────────────────────────────────────────────────────────────

export interface Skill {
  id: string
  name: string
  description: string
  category: string
  prompt_template?: string
  tags: string[]
  created_at?: string
  updated_at?: string
}

export interface SkillCategory {
  name: string
  count: number
}

// ─── Wiki ──────────────────────────────────────────────────────────────────────

export interface WikiPage {
  id: string
  title: string
  content: string
  tags: string[]
  category?: string
  created_at: string
  updated_at: string
}

// ─── Buddy ─────────────────────────────────────────────────────────────────────

export interface Buddy {
  id: string
  name: string
  species: string
  palette: string
  eye_shape: string
  accessories: string
  rarity: string
  stats: {
    friendliness: number
    wisdom: number
    energy: number
    curiosity: number
  }
  personality: {
    traits: string[]
    catchphrase: string
  }
  created_at: string
  updated_at: string
}

export interface BuddySpecies {
  name: string
  rarity: string
}

export interface BuddyOptions {
  species: BuddySpecies[]
  palettes: string[]
  eye_shapes: string[]
  accessories: string[]
}

// ─── Experiments / Autoresearch ────────────────────────────────────────────────

export const ExperimentStatus = {
  PENDING: "pending",
  RUNNING: "running",
  KEPT: "kept",
  DISCARDED: "discarded",
  CRASHED: "crashed",
} as const
export type ExperimentStatus = typeof ExperimentStatus[keyof typeof ExperimentStatus]

export interface ExperimentResult {
  id: string
  commit_hash: string
  val_bpb: number
  memory_gb: number
  status: ExperimentStatus
  description: string
  target_file: string
  diff_preview: string
  created_at: string
  duration_seconds: number
}

export interface ExperimentSession {
  id: string
  tag: string
  branch: string
  project_path: string
  target_file: string
  baseline?: ExperimentResult
  experiments: ExperimentResult[]
  best_bpb: number
  best_experiment_id?: string
  is_running: boolean
  time_budget: number
  total_runs: number
  created_at: string
  updated_at: string
  metadata: Record<string, unknown>
}

export interface ExperimentSessionSummary {
  id: string
  tag: string
  branch: string
  project_path: string
  target_file: string
  best_bpb: number
  is_running: boolean
  total_runs: number
  time_budget: number
  created_at: string
}

export interface ExperimentProposal {
  description: string
  code_change: string
  rationale: string
}

// ─── Notifications ─────────────────────────────────────────────────────────────

export interface Notification {
  id: string
  type: string
  title: string
  message: string
  read: boolean
  timestamp: string
}
