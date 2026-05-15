import type {
  Session,
  SessionSummary,
  Finding,
  ActivityLog,
  Config,
  HealthCheck,
  SoulTemplate,
  SoulState,
  Skill,
  WikiPage,
  Buddy,
  BuddyOptions,
  Notification,
  ExperimentSession,
  ExperimentSessionSummary,
  ExperimentProposal,
} from "@/types"
import { SessionMode } from "@/types"

export type { SoulFileType }

let _apiBase: string | null = null

async function _resolveApiBase(): Promise<string> {
  if (_apiBase !== null) return _apiBase

  // 1. Check for build-time env var
  if (import.meta.env.VITE_API_URL) {
    _apiBase = import.meta.env.VITE_API_URL as string
    return _apiBase
  }
  // 2. Check for Electron runtime
  try {
    const ea = (window as any).electronAPI
    if (ea?.getAppInfo) {
      const info = await ea.getAppInfo()
      if (info?.backendBase) {
        _apiBase = info.backendBase
        return _apiBase
      }
    }
  } catch {
    // ignore
  }
  // 3. Default: same origin
  _apiBase = ""
  return _apiBase
}

let _resolved = false
async function _ensureResolved() {
  if (!_resolved) {
    _resolved = true
    await _resolveApiBase()
  }
}

// Start resolving immediately (non-blocking)
_ensureResolved()

function getApiBase(): string {
  return _apiBase ?? ""
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const API_BASE = getApiBase()
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

// ─── Health & Config ───────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthCheck> {
  return request("/api/health")
}

export async function getConfig(): Promise<Config> {
  return request("/api/config")
}

export async function saveConfig(updates: Record<string, string>): Promise<Record<string, unknown>> {
  return request("/api/config", {
    method: "PUT",
    body: JSON.stringify(updates),
  })
}

// ─── Cache ────────────────────────────────────────────────────────────────────

export async function getCacheStats(): Promise<{ total: number; valid: number; expired: number }> {
  return request("/api/cache/stats")
}

export async function clearCache(): Promise<{ cleared: boolean }> {
  return request("/api/cache/clear", { method: "POST" })
}

// ─── Sessions ───────────────────────────────────────────────────────────────────

export async function listSessions(): Promise<SessionSummary[]> {
  return request("/api/sessions")
}

export async function getSession(sessionId: string): Promise<Session> {
  return request(`/api/sessions/${sessionId}`)
}

export async function createSession(
  projectPath: string,
  githubUrl = "",
  mode: SessionMode = SessionMode.AUDIT,
  goal = ""
): Promise<{ session_id: string; state: string }> {
  return request("/api/sessions", {
    method: "POST",
    body: JSON.stringify({
      project_path: projectPath,
      github_url: githubUrl,
      mode,
      goal,
    }),
  })
}

export async function getFindings(sessionId: string): Promise<Finding[]> {
  return request(`/api/sessions/${sessionId}/findings`)
}

export async function getActivity(sessionId: string, limit = 100): Promise<ActivityLog[]> {
  return request(`/api/sessions/${sessionId}/activity?limit=${limit}`)
}

// ─── Audit Operations ─────────────────────────────────────────────────────────

export async function ingest(sessionId: string): Promise<{ status: string; session_id: string }> {
  return request(`/api/sessions/${sessionId}/ingest`, { method: "POST" })
}

export async function startAudit(sessionId: string): Promise<{ status: string; session_id: string }> {
  return request(`/api/sessions/${sessionId}/audit`, { method: "POST" })
}

export async function fixFinding(
  sessionId: string,
  findingId: string
): Promise<{ status: string; finding_id: string }> {
  return request(`/api/sessions/${sessionId}/fix/${findingId}`, { method: "POST" })
}

export async function fixAll(
  sessionId: string
): Promise<{ status: string; finding_count: number }> {
  return request(`/api/sessions/${sessionId}/fix-all`, { method: "POST" })
}

// ─── Approval Flow ────────────────────────────────────────────────────────────

export async function approveFinding(
  sessionId: string,
  findingId: string,
  decision: "approve" | "reject" | "tweak",
  reason = "",
  tweakInstruction = ""
): Promise<{ status: string; finding_id: string }> {
  return request(`/api/sessions/${sessionId}/findings/${findingId}/approve`, {
    method: "POST",
    body: JSON.stringify({ decision, reason, tweak_instruction: tweakInstruction }),
  })
}

// ─── GitHub Integration ───────────────────────────────────────────────────────

export async function cloneRepo(
  sessionId: string
): Promise<{ status: string; url: string }> {
  return request(`/api/sessions/${sessionId}/clone`, { method: "POST" })
}

// ─── Report ───────────────────────────────────────────────────────────────────

export async function getReport(sessionId: string): Promise<Record<string, unknown>> {
  return request(`/api/sessions/${sessionId}/report`)
}

// ─── WebSocket ────────────────────────────────────────────────────────────────

const _wsKeepaliveMap = new WeakMap<WebSocket, ReturnType<typeof setInterval>>()

export function createWsConnection(
  sessionId: string,
  onMessage: (data: Record<string, unknown>) => void
): WebSocket {
  const base = getApiBase()
  let wsUrl: string
  if (base) {
    const wsProtocol = base.startsWith("https") ? "wss:" : "ws:"
    const hostPart = base.replace(/^https?:\/\//, "")
    wsUrl = `${wsProtocol}//${hostPart}/ws/${sessionId}`
  } else {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const isDev = window.location.port === "5173"
    const backendHost = isDev ? "127.0.0.1:8000" : window.location.host
    wsUrl = `${wsProtocol}//${backendHost}/ws/${sessionId}`
  }
  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping")
      } else {
        clearInterval(interval)
        _wsKeepaliveMap.delete(ws)
      }
    }, 30000)
    _wsKeepaliveMap.set(ws, interval)
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === "pong") return
      onMessage(data)
    } catch {
      // ignore parse errors
    }
  }

  ws.onerror = () => {
    // Silently ignore WS errors - they're common in dev mode with React StrictMode
  }

  return ws
}

export function closeWsConnection(ws: WebSocket | null): void {
  if (!ws) return
  const interval = _wsKeepaliveMap.get(ws)
  if (interval) {
    clearInterval(interval)
    _wsKeepaliveMap.delete(ws)
  }
  ws.close()
}

// ─── Fast File Search (fff.nvim-inspired) ───────────────────────────────────────

export async function searchFiles(
  root: string, query: string, mode = "fuzzy",
  extensions?: string, maxResults = 30
): Promise<Array<{ path: string; score: number; mode: string; matches?: number; context?: Array<{ line: number; snippet: string }> }>> {
  const params = new URLSearchParams({ root, query, mode, max_results: String(maxResults) })
  if (extensions) params.set("extensions", extensions)
  return request(`/api/search/files?${params}`)
}

export async function searchSymbols(root: string, query: string, extensions?: string): Promise<Array<{ path: string; symbol: string; line: number }>> {
  const params = new URLSearchParams({ root, query })
  if (extensions) params.set("extensions", extensions)
  return request(`/api/search/symbols?${params}`)
}

export async function getRecentFiles(root = "", limit = 20): Promise<Array<{ path: string; score: number; access_count: number; last_access: string }>> {
  return request(`/api/search/recent?root=${encodeURIComponent(root)}&limit=${limit}`)
}

// ─── Context Optimizer (context-mode-inspired) ──────────────────────────────────

export async function optimizeContext(
  content: string, tool = "unknown", type = "text", maxChars = 500
): Promise<{ compressed: string }> {
  return request("/api/context/optimize", {
    method: "POST",
    body: JSON.stringify({ content, tool, type, max_chars: maxChars }),
  })
}

export async function trackSessionEvent(sessionId: string, eventType: string, summary: string, detail = ""): Promise<{ status: string }> {
  return request("/api/context/session-event", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, event_type: eventType, summary, detail }),
  })
}

export async function getSessionContext(sessionId: string): Promise<{ events: Array<Record<string, unknown>>; summary: string }> {
  return request(`/api/context/session/${sessionId}`)
}

export async function getContextStats(): Promise<{
  total_raw_chars: number; total_compressed_chars: number; sandbox_calls: number;
  savings_percent: number; savings_by_tool: Record<string, { calls: number; raw_chars: number; compressed_chars: number }>
}> {
  return request("/api/context/stats")
}

export async function resetContextStats(): Promise<{ status: string }> {
  return request("/api/context/reset-stats", { method: "POST" })
}

// ─── Knowledge Graph (Understand-Anything + graphify-inspired) ──────────────────

export async function scanProjectGraph(projectPath: string): Promise<{ nodes: Array<Record<string, unknown>>; edges: Array<Record<string, unknown>> }> {
  return request("/api/graph/scan", {
    method: "POST",
    body: JSON.stringify({ project_path: projectPath }),
  })
}

export async function loadProjectGraph(projectPath: string): Promise<{ graph: { nodes: Array<Record<string, unknown>>; edges: Array<Record<string, unknown>> }; architecture: Record<string, unknown> }> {
  return request(`/api/graph/load?project_path=${encodeURIComponent(projectPath)}`)
}

export async function listKnowledgeGraphs(): Promise<Array<{ name: string; nodes: number; edges: number; layers: Record<string, number>; node_types: Record<string, number>; updated: string }>> {
  return request("/api/graph/list")
}

export async function queryKnowledgeGraph(projectPath: string, nodeType?: string, search?: string): Promise<{ nodes: Array<Record<string, unknown>>; edges: Array<Record<string, unknown>> }> {
  const params = new URLSearchParams({ project_path: projectPath })
  if (nodeType) params.set("node_type", nodeType)
  if (search) params.set("search", search)
  return request(`/api/graph/query?${params}`)
}

export async function getFileDependencies(projectPath: string, filePath: string): Promise<{ imports: Array<Record<string, unknown>>; dependents: Array<string> }> {
  return request(`/api/graph/dependencies?project_path=${encodeURIComponent(projectPath)}&file_path=${encodeURIComponent(filePath)}`)
}

// ─── Code Extractor (distil-inspired L1-L5) ────────────────────────────────────

export async function extractAst(filePath: string): Promise<Record<string, unknown>> {
  return request("/api/extract/ast", {
    method: "POST",
    body: JSON.stringify({ file_path: filePath }),
  })
}

export async function extractCallGraph(projectPath: string, filePaths?: string[]): Promise<Record<string, unknown>> {
  return request("/api/extract/call-graph", {
    method: "POST",
    body: JSON.stringify({ project_path: projectPath, file_paths: filePaths }),
  })
}

export async function extractControlFlow(filePath: string, functionName?: string): Promise<Record<string, unknown>> {
  return request("/api/extract/cfg", {
    method: "POST",
    body: JSON.stringify({ file_path: filePath, function_name: functionName }),
  })
}

export async function extractSlice(filePath: string, targetLine: number, direction = "backward"): Promise<Record<string, unknown>> {
  return request("/api/extract/slice", {
    method: "POST",
    body: JSON.stringify({ file_path: filePath, target_line: targetLine, direction }),
  })
}

export async function extractAllLayers(filePath: string): Promise<Record<string, unknown>> {
  return request("/api/extract/all", {
    method: "POST",
    body: JSON.stringify({ file_path: filePath }),
  })
}

// ─── Design System (ui-ux-pro-max + huashu + taste-skill) ───────────────────────

export async function listDesignStyles(tag?: string): Promise<Array<{ name: string; description: string; css: string; tags: string[] }>> {
  const params = tag ? `?tag=${tag}` : ""
  return request(`/api/design/styles${params}`)
}

export async function listDesignPalettes(industry?: string): Promise<Array<{ name: string; colors: string[]; industry: string[] }>> {
  const params = industry ? `?industry=${industry}` : ""
  return request(`/api/design/palettes${params}`)
}

export async function listFontPairings(mood?: string): Promise<Array<{ heading: string; body: string; mood: string }>> {
  const params = mood ? `?mood=${mood}` : ""
  return request(`/api/design/fonts${params}`)
}

export async function suggestDesign(projectType = "web"): Promise<Record<string, unknown>> {
  return request("/api/design/suggest", {
    method: "POST",
    body: JSON.stringify({ project_type: projectType }),
  })
}

export async function generatePrototype(data: {
  title: string; screens: Array<{ name: string; content: string }>;
  style?: string; palette?: string; font?: string; mobile_frame?: boolean;
}): Promise<{ html: string; title: string; screens: number; size_bytes: number }> {
  return request("/api/design/prototype", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function generateSlides(data: {
  title: string; slides: Array<{ title: string; content: string }>; palette?: string;
}): Promise<{ html: string; title: string; slides: number; size_bytes: number }> {
  return request("/api/design/slides", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function generateDesignReview(data: {
  project_name: string; issues: Array<{ title: string; description: string; severity: string }>; palette?: string; save_path?: string;
}): Promise<{ html: string; size: number }> {
  return request("/api/design/review", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

// ─── Spec-Driven Development (spec-kit) ─────────────────────────────────────────

export async function createSpec(data: { project_name: string; goal: string; context?: string; requirements?: string[] }): Promise<Record<string, unknown>> {
  return request("/api/spec/create", { method: "POST", body: JSON.stringify(data) })
}

export async function generateSpecTasks(specId: string): Promise<Record<string, unknown>> {
  return request(`/api/spec/${specId}/tasks`, { method: "POST" })
}

export async function implementTask(specId: string, taskId: string, projectPath: string): Promise<Record<string, unknown>> {
  return request(`/api/spec/${specId}/implement/${taskId}`, {
    method: "POST", body: JSON.stringify({ project_path: projectPath }),
  })
}

export async function applySpecImplementation(projectPath: string, files: Array<{ path: string; content: string }>): Promise<Record<string, unknown>> {
  return request("/api/spec/apply", {
    method: "POST", body: JSON.stringify({ project_path: projectPath, files }),
  })
}

export async function listSpecs(): Promise<Array<{ id: string; project: string; goal: string; status: string; created_at: string }>> {
  return request("/api/spec/list")
}

export async function getSpec(specId: string): Promise<Record<string, unknown>> {
  return request(`/api/spec/${specId}`)
}

// ─── Voice Interface (VibeVoice) ────────────────────────────────────────────────

export async function getVoiceStatus(): Promise<{ available_backends: string[]; detected_backend: string; voices: string[]; has_vibevoice_key: boolean; has_elevenlabs_key: boolean }> {
  return request("/api/voice/status")
}

export async function speakVoice(text: string, voice = "default", backend = "auto"): Promise<Record<string, unknown>> {
  return request("/api/voice/speak", {
    method: "POST", body: JSON.stringify({ text, voice, backend }),
  })
}

// ─── LLM Optimizer (TurboQuant) ────────────────────────────────────────────────

export async function getOptimizerConfig(model = "", vram = 0): Promise<Record<string, unknown>> {
  return request(`/api/optimizer/config?model=${encodeURIComponent(model)}&vram=${vram}`)
}

export async function getOptimizationStrategies(): Promise<Record<string, { name: string; description: string; compression_ratio: number; quality_impact: string }>> {
  return request("/api/optimizer/strategies")
}

export async function getServingCommand(model = "", port = 8000): Promise<{ command: string }> {
  return request(`/api/optimizer/serving-command?model=${encodeURIComponent(model)}&port=${port}`)
}

// ─── openvscode-server ──────────────────────────────────────────────────────────

export async function getVscodeStatus(): Promise<{ available: boolean; port: number; command: string; install_url?: string; install_command?: string }> {
  return request("/api/vscode/status")
}

// ─── Voice Commands ──────────────────────────────────────────────────────────────

export async function executeVoiceCommand(text: string): Promise<Record<string, unknown>> {
  return request("/api/voice/command", {
    method: "POST",
    body: JSON.stringify({ text }),
  })
}

export async function getVoiceHelp(): Promise<{ help: string }> {
  return request("/api/voice/help")
}

// ─── Agent Loop (HALO-style self-improvement) ───────────────────────────────────

export async function recordAgentTrace(data: {
  session_id: string; run_id: string; agent_name: string; action: string;
  tool?: string; duration_ms?: number; tokens_in?: number; tokens_out?: number;
  success?: boolean; error?: string;
}): Promise<{ trace_id: number }> {
  return request("/api/loop/trace", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function getAgentTraces(sessionId = "", limit = 100): Promise<Array<Record<string, unknown>>> {
  return request(`/api/loop/traces?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`)
}

export async function analyzeAgentTraces(sessionId = ""): Promise<Record<string, unknown>> {
  return request(`/api/loop/analyze?session_id=${encodeURIComponent(sessionId)}`)
}

export async function generateAgentImprovements(sessionId = ""): Promise<Array<Record<string, unknown>>> {
  return request("/api/loop/improvements/generate", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export async function getAgentImprovements(sessionId = ""): Promise<Array<Record<string, unknown>>> {
  return request(`/api/loop/improvements?session_id=${encodeURIComponent(sessionId)}`)
}

export async function applyAgentImprovement(impId: number, targetFile = ""): Promise<Record<string, unknown>> {
  return request(`/api/loop/improvements/${impId}/apply`, {
    method: "POST",
    body: JSON.stringify({ target_file: targetFile }),
  })
}

export async function runImprovementLoop(sessionId = "", targetFile = "", iterations = 3): Promise<Array<Record<string, unknown>>> {
  return request("/api/loop/run", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, target_file: targetFile, iterations }),
  })
}

export async function getLoopBenchmarks(improvementId?: number): Promise<Array<Record<string, unknown>>> {
  const params = improvementId ? `?improvement_id=${improvementId}` : ""
  return request(`/api/loop/benchmarks${params}`)
}

// ─── Experiments / Autoresearch ─────────────────────────────────────────────────

export async function listExperimentSessions(): Promise<ExperimentSessionSummary[]> {
  return request("/api/experiments/sessions")
}

export async function createExperimentSession(data: {
  project_path: string
  target_file?: string
  tag?: string
  time_budget?: number
}): Promise<{ id: string; tag: string; branch: string; target_file: string; time_budget: number }> {
  return request("/api/experiments/sessions", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function getExperimentSession(sessionId: string): Promise<ExperimentSession> {
  return request(`/api/experiments/sessions/${sessionId}`)
}

export async function deleteExperimentSession(sessionId: string): Promise<{ status: string }> {
  return request(`/api/experiments/sessions/${sessionId}`, { method: "DELETE" })
}

export async function establishBaseline(sessionId: string): Promise<Record<string, unknown>> {
  return request(`/api/experiments/sessions/${sessionId}/baseline`, { method: "POST" })
}

export async function runExperiment(
  sessionId: string,
  description: string,
  codeChange = ""
): Promise<Record<string, unknown>> {
  return request(`/api/experiments/sessions/${sessionId}/run`, {
    method: "POST",
    body: JSON.stringify({ description, code_change: codeChange }),
  })
}

export async function proposeExperiment(sessionId: string): Promise<ExperimentProposal> {
  return request(`/api/experiments/sessions/${sessionId}/propose`, { method: "POST" })
}

export async function getExperimentResults(sessionId: string): Promise<{ tsv: string }> {
  return request(`/api/experiments/sessions/${sessionId}/results`)
}

export async function selfModifyAgent(sessionId: string, agentFile: string): Promise<Record<string, unknown>> {
  return request("/api/experiments/self-modify", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, agent_file: agentFile }),
  })
}

// ─── Soul ───────────────────────────────────────────────────────────────────────

export async function getActiveSoul(): Promise<SoulState> {
  return request("/api/soul/active")
}

export async function getSoulTemplates(): Promise<SoulTemplate[]> {
  return request("/api/soul/templates")
}

export async function applySoulTemplate(templateId: string): Promise<{ status: string }> {
  return request(`/api/soul/apply-template/${templateId}`, { method: "POST" })
}

export async function getSoulFile(type: string): Promise<{ content: string }> {
  return request(`/api/soul/file/${type}`)
}

export async function updateSoulFile(type: string, content: string): Promise<{ status: string }> {
  return request(`/api/soul/file/${type}`, {
    method: "PUT",
    body: JSON.stringify({ content }),
  })
}

// ─── Skills ─────────────────────────────────────────────────────────────────────

export async function getSkills(params?: { category?: string; search?: string }): Promise<Skill[]> {
  const query = new URLSearchParams()
  if (params?.category) query.set("category", params.category)
  if (params?.search) query.set("search", params.search)
  const qs = query.toString()
  return request(`/api/skills${qs ? `?${qs}` : ""}`)
}

export async function getSkill(id: string): Promise<Skill> {
  return request(`/api/skills/${id}`)
}

// ─── Wiki ───────────────────────────────────────────────────────────────────────

export async function searchWiki(query: string): Promise<WikiPage[]> {
  return request(`/api/wiki/search?q=${encodeURIComponent(query)}`)
}

export async function getWikiPages(): Promise<WikiPage[]> {
  return request("/api/wiki/pages")
}

export async function getWikiPage(id: string): Promise<WikiPage> {
  return request(`/api/wiki/page/${id}`)
}

export async function createWikiPage(data: { title: string; content: string; tags?: string[] }): Promise<WikiPage> {
  return request("/api/wiki/page", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function updateWikiPage(id: string, data: { title?: string; content?: string; tags?: string[] }): Promise<WikiPage> {
  return request(`/api/wiki/page/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  })
}

export async function deleteWikiPage(id: string): Promise<{ status: string }> {
  return request(`/api/wiki/page/${id}`, { method: "DELETE" })
}

// ─── Buddy ──────────────────────────────────────────────────────────────────────

export async function getBuddy(): Promise<Buddy | null> {
  return request("/api/buddy")
}

export async function createBuddy(data: {
  name: string
  species: string
  palette: string
  eye_shape: string
  accessories: string
}): Promise<Buddy> {
  return request("/api/buddy/create", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function updateBuddy(data: Partial<{
  name: string
  species: string
  palette: string
  eye_shape: string
  accessory: string
}>): Promise<Buddy> {
  return request("/api/buddy/update", {
    method: "PUT",
    body: JSON.stringify(data),
  })
}

export async function getBuddyOptions(): Promise<BuddyOptions> {
  return request("/api/buddy/options")
}

// ─── Notifications ──────────────────────────────────────────────────────────────

export async function getNotifications(): Promise<Notification[]> {
  return request("/api/notifications")
}

export async function markNotificationRead(id: string): Promise<{ status: string }> {
  return request(`/api/notifications/${id}/read`, { method: "POST" })
}

export async function clearNotifications(): Promise<{ status: string }> {
  return request("/api/notifications/clear", { method: "POST" })
}

// ─── Swarm ────────────────────────────────────────────────────────────────────

export const SWARM_API_BASE = "/api/swarm"

export async function getSwarmStatus(): Promise<any> {
  return request(`${SWARM_API_BASE}/api/swarm/status`)
}

export async function listSwarmAgents(): Promise<any> {
  return request(`${SWARM_API_BASE}/api/swarm/agents`)
}

export async function getSwarmActivity(limit = 50): Promise<any> {
  return request(`${SWARM_API_BASE}/api/swarm/activity?limit=${limit}`)
}

export async function submitSwarmTask(data: { description: string; task_type?: string; requirements?: string[]; priority?: string }): Promise<any> {
  return request(`${SWARM_API_BASE}/api/swarm/tasks`, {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function switchSwarmModel(data: { agent_id?: string; model: string }): Promise<any> {
  return request(`${SWARM_API_BASE}/api/swarm/models/switch`, {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function callRoundTable(data: { topic: string; question: string; agents?: string[] }): Promise<any> {
  return request(`${SWARM_API_BASE}/api/swarm/round-table`, {
    method: "POST",
    body: JSON.stringify(data),
  })
}
