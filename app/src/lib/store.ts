import { create } from "zustand"
import type { Session, SessionSummary, Finding, ActivityLog, Config, HealthCheck, SoulTemplate, SoulState, Skill, WikiPage, Buddy, BuddyOptions, Notification, ExperimentSession, ExperimentSessionSummary, ExperimentProposal } from "@/types"
import * as api from "@/lib/api"
import { closeWsConnection } from "@/lib/api"
import { computeUnreadCount } from "@/lib/notifications"

interface AppState {
  // Health & Config
  health: HealthCheck | null
  config: Config | null

  // Sessions
  sessions: SessionSummary[]
  currentSession: Session | null
  currentFindings: Finding[]
  currentActivity: ActivityLog[]
  loading: boolean
  error: string | null

  // WebSocket
  ws: WebSocket | null
  _refreshPending: boolean
  _pollInterval: ReturnType<typeof setInterval> | null

  // Soul
  activeSoul: SoulState | null
  soulTemplates: SoulTemplate[]
  soulLoading: boolean
  soulEditing: { type: string; content: string } | null

  // Skills
  skills: Skill[]
  skillsLoading: boolean
  skillSearch: string
  skillCategoryFilter: string

  // Wiki
  wikiPages: WikiPage[]
  currentWikiPage: WikiPage | null
  wikiSearchResults: WikiPage[]
  wikiLoading: boolean

  // Buddy
  buddy: Buddy | null
  buddyOptions: BuddyOptions | null
  buddyLoading: boolean

  // Autoresearch / Experiments
  experimentSessions: ExperimentSessionSummary[]
  currentExperiment: ExperimentSession | null
  experimentProposal: ExperimentProposal | null
  experimentResultsTsv: string
  experimentLoading: boolean

  // Notifications
  notifications: Notification[]
  unreadCount: number
  notifLoading: boolean

  // Actions
  buddyMood: string
  buddyMessage: string
  sessionActivity: string
  agentExecNodes: any[]
  fetchHealth: () => Promise<void>
  fetchConfig: () => Promise<void>
  fetchSessions: () => Promise<void>
  selectSession: (sessionId: string) => Promise<void>
  createSession: (projectPath: string, githubUrl?: string, mode?: string, goal?: string) => Promise<string>
  startIngest: (sessionId: string) => Promise<void>
  startAudit: (sessionId: string) => Promise<void>
  fixFinding: (sessionId: string, findingId: string) => Promise<void>
  fixAll: (sessionId: string) => Promise<void>
  approveFinding: (sessionId: string, findingId: string, decision: string, reason?: string, tweakInstruction?: string) => Promise<void>
  connectWebSocket: (sessionId: string) => void
  disconnectWebSocket: () => void
  startPolling: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  refreshSession: () => Promise<void>

  // Soul actions
  fetchActiveSoul: () => Promise<void>
  fetchSoulTemplates: () => Promise<void>
  applySoulTemplate: (templateId: string) => Promise<void>
  openSoulFile: (type: string) => Promise<void>
  saveSoulFile: (type: string, content: string) => Promise<void>
  closeSoulEditor: () => void

  // Skills actions
  fetchSkills: () => Promise<void>
  setSkillSearch: (search: string) => Promise<void>
  setSkillCategoryFilter: (category: string) => Promise<void>

  // Wiki actions
  fetchWikiPages: () => Promise<void>
  selectWikiPage: (id: string) => Promise<void>
  searchWiki: (query: string) => Promise<void>
  createWikiPage: (data: { title: string; content: string; tags?: string[] }) => Promise<WikiPage | null>
  updateWikiPage: (id: string, data: { title?: string; content?: string; tags?: string[] }) => Promise<void>
  deleteWikiPage: (id: string) => Promise<void>
  setCurrentWikiPage: (page: WikiPage | null) => void

  // Buddy actions
  fetchBuddy: () => Promise<void>
  fetchBuddyOptions: () => Promise<void>
  createBuddy: (data: { name: string; species: string; palette: string; eye_shape: string; accessories: string }) => Promise<void>
  updateBuddy: (data: Partial<{ name: string; species: string; palette: string; eye_shape: string; accessories: string }>) => Promise<void>
  setBuddyMood: (mood: string) => void
  setBuddyMessage: (msg: string) => void

  // Voice actions
  voiceListening: boolean
  speakText: string
  setSpeakText: (text: string) => void
  processVoiceCommand: (text: string) => Promise<void>

  // Agent Execution Visualization
  addAgentExecNode: (node: { id: string; label: string; type: string; status: string; duration_ms?: number; depth: number }) => void
  updateAgentExecNode: (id: string, updates: Partial<{ status: string; duration_ms: number }>) => void
  clearAgentExecNodes: () => void
  setSessionActivity: (msg: string) => void

  // File Search actions
  searchFiles: (root: string, query: string, mode?: string) => Promise<void>
  searchSymbols: (root: string, query: string) => Promise<void>
  fetchRecentFiles: (root?: string) => Promise<void>
  clearSearch: () => void
  searchResults: Array<{ path: string; score: number; mode: string; matches?: number }>
  searchSymbolResults: Array<{ path: string; symbol: string; line: number }>
  recentFiles: Array<{ path: string; score: number; access_count: number; last_access: string }>
  searchLoading: boolean
  searchQuery: string
  searchMode: string

  // Context Optimizer actions
  fetchContextStats: () => Promise<void>
  resetContextStats: () => Promise<void>
  contextStats: { total_raw_chars: number; total_compressed_chars: number; sandbox_calls: number; savings_percent: number; savings_by_tool: Record<string, { calls: number; raw_chars: number; compressed_chars: number }> } | null

  // Experiment / Autoresearch actions
  fetchExperimentSessions: () => Promise<void>
  createExperimentSession: (data: { project_path: string; target_file?: string; tag?: string; time_budget?: number }) => Promise<string | null>
  selectExperimentSession: (id: string) => Promise<void>
  deleteExperimentSession: (id: string) => Promise<void>
  establishBaseline: (id: string) => Promise<void>
  runExperiment: (id: string, description: string, codeChange?: string) => Promise<void>
  proposeExperiment: (id: string) => Promise<void>
  fetchExperimentResults: (id: string) => Promise<void>
  selfModifyAgent: (id: string, agentFile: string) => Promise<void>
  setExperimentProposal: (proposal: ExperimentProposal | null) => void

  // Notification actions
  fetchNotifications: () => Promise<void>
  markNotificationRead: (id: string) => Promise<void>
  clearNotifications: () => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  health: null,
  config: null,
  sessions: [],
  currentSession: null,
  currentFindings: [],
  currentActivity: [],
  loading: false,
  error: null,
  ws: null,
  _refreshPending: false,
  _pollInterval: null,

  // Soul state
  activeSoul: null,
  soulTemplates: [],
  soulLoading: false,
  soulEditing: null,

  // Skills state
  skills: [],
  skillsLoading: false,
  skillSearch: "",
  skillCategoryFilter: "",

  // Wiki state
  wikiPages: [],
  currentWikiPage: null,
  wikiSearchResults: [],
  wikiLoading: false,

  // Buddy state
  buddy: null,
  buddyOptions: null,
  buddyLoading: false,
  buddyMood: "idle",
  buddyMessage: "",

  // Voice state
  speakText: "",
  voiceListening: false,

  // Agent Execution Visualization
  agentExecNodes: [],
  sessionActivity: "",

  // File Search state
  searchResults: [],
  searchSymbolResults: [],
  recentFiles: [],
  searchLoading: false,
  searchQuery: "",
  searchMode: "fuzzy",

  // Context Optimizer state
  contextStats: null,

  // Autoresearch / Experiments state
  experimentSessions: [],
  currentExperiment: null,
  experimentProposal: null,
  experimentResultsTsv: "",
  experimentLoading: false,

  // Notifications state
  notifications: [],
  unreadCount: 0,
  notifLoading: false,

  fetchHealth: async () => {
    try {
      const health = await api.getHealth()
      set({ health })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  fetchConfig: async () => {
    try {
      const config = await api.getConfig()
      set({ config })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  fetchSessions: async () => {
    try {
      set({ loading: true })
      const sessions = await api.listSessions()
      set({ sessions, loading: false })
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
    }
  },

  selectSession: async (sessionId: string) => {
    try {
      set({ loading: true })
      const [session, findings, activity] = await Promise.all([
        api.getSession(sessionId),
        api.getFindings(sessionId),
        api.getActivity(sessionId),
      ])
      set({
        currentSession: session,
        currentFindings: findings,
        currentActivity: activity,
        loading: false,
      })
      // Connect WebSocket for real-time updates (delayed to avoid React StrictMode double-invocation issues)
      setTimeout(() => get().connectWebSocket(sessionId), 100)
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
    }
  },

  createSession: async (projectPath: string, githubUrl = "", mode = "audit", goal = "") => {
    try {
      set({ loading: true })
      const result = await api.createSession(projectPath, githubUrl, mode as any, goal)
      await get().fetchSessions()
      set({ loading: false })
      return result.session_id
    } catch (error) {
      set({ error: (error as Error).message, loading: false })
      throw error
    }
  },

  startIngest: async (sessionId: string) => {
    try {
      await api.ingest(sessionId)
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  startAudit: async (sessionId: string) => {
    try {
      await api.startAudit(sessionId)
      await get().refreshSession()
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  fixFinding: async (sessionId: string, findingId: string) => {
    try {
      await api.fixFinding(sessionId, findingId)
      await get().refreshSession()
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  fixAll: async (sessionId: string) => {
    try {
      await api.fixAll(sessionId)
      await get().refreshSession()
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  approveFinding: async (sessionId: string, findingId: string, decision: string, reason = "", tweakInstruction = "") => {
    try {
      await api.approveFinding(sessionId, findingId, decision as any, reason, tweakInstruction)
      await get().refreshSession()
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  connectWebSocket: (sessionId: string) => {
    const { ws: existing, _pollInterval } = get()
    if (_pollInterval) {
      clearInterval(_pollInterval)
    }
    closeWsConnection(existing)

    const ws = api.createWsConnection(sessionId, () => {
      get().refreshSession()
    })

    set({ ws, _pollInterval: null })
  },

  startPolling: () => {
    const { _pollInterval } = get()
    if (_pollInterval) return
    const interval = setInterval(() => {
      get().refreshSession()
    }, 5000)
    set({ _pollInterval: interval })
  },

  disconnectWebSocket: () => {
    const { ws, _pollInterval } = get()
    if (_pollInterval) {
      clearInterval(_pollInterval)
    }
    closeWsConnection(ws)
    set({ ws: null, _pollInterval: null })
  },

  refreshSession: async () => {
    const { currentSession, _refreshPending } = get()
    if (!currentSession || _refreshPending) return
    set({ _refreshPending: true })
    try {
      const [updatedSession, findings, activity] = await Promise.all([
        api.getSession(currentSession.id),
        api.getFindings(currentSession.id),
        api.getActivity(currentSession.id),
      ])
      set({
        currentSession: updatedSession,
        currentFindings: findings,
        currentActivity: activity,
        error: null,
      })
    } catch (err) {
      console.warn("Session refresh failed:", err)
    } finally {
      set({ _refreshPending: false })
    }
  },

  setLoading: (loading: boolean) => set({ loading }),
  setError: (error: string | null) => set({ error }),

  // ─── Soul Actions ───────────────────────────────────────────────────────────

  fetchActiveSoul: async () => {
    try {
      set({ soulLoading: true })
      const activeSoul = await api.getActiveSoul()
      set({ activeSoul, soulLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, soulLoading: false })
    }
  },

  fetchSoulTemplates: async () => {
    try {
      set({ soulLoading: true })
      const soulTemplates = await api.getSoulTemplates()
      set({ soulTemplates, soulLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, soulLoading: false })
    }
  },

  applySoulTemplate: async (templateId: string) => {
    try {
      set({ soulLoading: true })
      await api.applySoulTemplate(templateId)
      await get().fetchActiveSoul()
      set({ soulLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, soulLoading: false })
    }
  },

  openSoulFile: async (type: string) => {
    try {
      const result = await api.getSoulFile(type)
      set({ soulEditing: { type, content: result.content } })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  saveSoulFile: async (type: string, content: string) => {
    try {
      await api.updateSoulFile(type, content)
      set({ soulEditing: null })
      await get().fetchActiveSoul()
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  closeSoulEditor: () => set({ soulEditing: null }),

  // ─── Skills Actions ─────────────────────────────────────────────────────────

  fetchSkills: async () => {
    try {
      set({ skillsLoading: true })
      const { skillCategoryFilter, skillSearch } = get()
      const skills = await api.getSkills({
        category: skillCategoryFilter || undefined,
        search: skillSearch || undefined,
      })
      set({ skills, skillsLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, skillsLoading: false })
    }
  },

  setSkillSearch: async (search: string) => {
    set({ skillSearch: search })
    await get().fetchSkills()
  },

  setSkillCategoryFilter: async (category: string) => {
    set({ skillCategoryFilter: category })
    await get().fetchSkills()
  },

  // ─── Wiki Actions ────────────────────────────────────────────────────────────

  fetchWikiPages: async () => {
    try {
      set({ wikiLoading: true })
      const wikiPages = await api.getWikiPages()
      set({ wikiPages, wikiLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, wikiLoading: false })
    }
  },

  selectWikiPage: async (id: string) => {
    try {
      set({ wikiLoading: true })
      const currentWikiPage = await api.getWikiPage(id)
      set({ currentWikiPage, wikiLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, wikiLoading: false })
    }
  },

  searchWiki: async (query: string) => {
    try {
      set({ wikiLoading: true })
      const wikiSearchResults = await api.searchWiki(query)
      set({ wikiSearchResults, wikiLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, wikiLoading: false })
    }
  },

  createWikiPage: async (data: { title: string; content: string; tags?: string[] }) => {
    try {
      set({ wikiLoading: true })
      const page = await api.createWikiPage(data)
      await get().fetchWikiPages()
      set({ currentWikiPage: page, wikiLoading: false })
      return page
    } catch (error) {
      set({ error: (error as Error).message, wikiLoading: false })
      return null
    }
  },

  updateWikiPage: async (id: string, data: { title?: string; content?: string; tags?: string[] }) => {
    try {
      set({ wikiLoading: true })
      const page = await api.updateWikiPage(id, data)
      set({ currentWikiPage: page, wikiLoading: false })
      await get().fetchWikiPages()
    } catch (error) {
      set({ error: (error as Error).message, wikiLoading: false })
    }
  },

  deleteWikiPage: async (id: string) => {
    try {
      await api.deleteWikiPage(id)
      set({ currentWikiPage: null })
      await get().fetchWikiPages()
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  setCurrentWikiPage: (page: WikiPage | null) => set({ currentWikiPage: page }),

  // ─── Buddy Actions ───────────────────────────────────────────────────────────

  fetchBuddy: async () => {
    try {
      set({ buddyLoading: true })
      const buddy = await api.getBuddy()
      set({ buddy, buddyLoading: false })
    } catch {
      set({ buddy: null, buddyLoading: false })
    }
  },

  fetchBuddyOptions: async () => {
    try {
      const buddyOptions = await api.getBuddyOptions()
      set({ buddyOptions })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  createBuddy: async (data: { name: string; species: string; palette: string; eye_shape: string; accessories: string }) => {
    try {
      set({ buddyLoading: true })
      const buddy = await api.createBuddy(data)
      set({ buddy, buddyLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, buddyLoading: false })
    }
  },

  updateBuddy: async (data: Partial<{ name: string; species: string; palette: string; eye_shape: string; accessories: string }>) => {
    try {
      set({ buddyLoading: true })
      const buddy = await api.updateBuddy(data)
      set({ buddy, buddyLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, buddyLoading: false })
    }
  },

  setBuddyMood: (mood: string) => set({ buddyMood: mood }),
  setBuddyMessage: (msg: string) => set({ buddyMessage: msg }),

  // ─── Voice Actions ────────────────────────────────────────────────────────────────

  setSpeakText: (text: string) => set({ speakText: text }),

  processVoiceCommand: async (text: string) => {
    try {
      set({ voiceListening: true, buddyMood: "thinking", buddyMessage: `Processing: "${text.slice(0, 30)}..."` })
      const res = await api.executeVoiceCommand(text)
      const responseText = (res as any)?.spoken_response || "Done"
      set({ speakText: responseText, buddyMood: "happy", buddyMessage: responseText, voiceListening: false })
      if ((res as any)?.action && (res as any).action !== "unknown" && (res as any).action !== "help") {
        setTimeout(() => set({ buddyMood: "idle" }), 3000)
      }
    } catch {
      set({ buddyMood: "error", buddyMessage: "Command failed", voiceListening: false })
    }
  },

  // ─── Agent Execution Visualization ────────────────────────────────────────────────

  addAgentExecNode: (node) => {
    const { agentExecNodes } = get()
    set({ agentExecNodes: [...agentExecNodes, { ...node, id: `${node.id}-${Date.now()}` }] })
  },

  updateAgentExecNode: (id, updates) => {
    const { agentExecNodes } = get()
    set({ agentExecNodes: agentExecNodes.map((n) => n.id === id ? { ...n, ...updates } : n) })
  },

  clearAgentExecNodes: () => set({ agentExecNodes: [] }),

  setSessionActivity: (msg) => {
    set({ sessionActivity: msg })
    set({ buddyMessage: msg, buddyMood: "working" })
    setTimeout(() => {
      const { buddyMood } = get()
      if (buddyMood === "working") set({ buddyMood: "idle" })
    }, 4000)
  },

  // ─── File Search Actions ────────────────────────────────────────────────────────

  searchFiles: async (root: string, query: string, mode = "fuzzy") => {
    try {
      set({ searchLoading: true, searchQuery: query, searchMode: mode })
      const searchResults = await api.searchFiles(root, query, mode)
      set({ searchResults, searchLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, searchLoading: false })
    }
  },

  searchSymbols: async (root: string, query: string) => {
    try {
      set({ searchLoading: true })
      const results = await api.searchSymbols(root, query)
      set({ searchSymbolResults: results, searchLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, searchLoading: false })
    }
  },

  fetchRecentFiles: async (root = "") => {
    try {
      const recentFiles = await api.getRecentFiles(root)
      set({ recentFiles })
    } catch {
      // silent
    }
  },

  clearSearch: () => set({ searchResults: [], searchSymbolResults: [], searchQuery: "" }),

  // ─── Context Optimizer Actions ──────────────────────────────────────────────────

  fetchContextStats: async () => {
    try {
      const contextStats = await api.getContextStats()
      set({ contextStats })
    } catch {
      // silent
    }
  },

  resetContextStats: async () => {
    try {
      await api.resetContextStats()
      set({ contextStats: { total_raw_chars: 0, total_compressed_chars: 0, sandbox_calls: 0, savings_percent: 0, savings_by_tool: {} } })
    } catch {
      // silent
    }
  },

  // ─── Experiment / Autoresearch Actions ────────────────────────────────────────

  fetchExperimentSessions: async () => {
    try {
      set({ experimentLoading: true })
      const experimentSessions = await api.listExperimentSessions()
      set({ experimentSessions, experimentLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, experimentLoading: false })
    }
  },

  createExperimentSession: async (data) => {
    try {
      set({ experimentLoading: true })
      const result = await api.createExperimentSession(data)
      await get().fetchExperimentSessions()
      set({ experimentLoading: false })
      return result.id
    } catch (error) {
      set({ error: (error as Error).message, experimentLoading: false })
      return null
    }
  },

  selectExperimentSession: async (id) => {
    try {
      set({ experimentLoading: true })
      const session = await api.getExperimentSession(id)
      const tsvResult = await api.getExperimentResults(id)
      set({
        currentExperiment: session,
        experimentResultsTsv: tsvResult.tsv,
        experimentLoading: false,
      })
    } catch (error) {
      set({ error: (error as Error).message, experimentLoading: false })
    }
  },

  deleteExperimentSession: async (id) => {
    try {
      await api.deleteExperimentSession(id)
      await get().fetchExperimentSessions()
      set({ currentExperiment: null })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  establishBaseline: async (id) => {
    try {
      set({ experimentLoading: true })
      await api.establishBaseline(id)
      await get().selectExperimentSession(id)
      set({ experimentLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, experimentLoading: false })
    }
  },

  runExperiment: async (id, description, codeChange = "") => {
    try {
      set({ experimentLoading: true })
      await api.runExperiment(id, description, codeChange)
      await get().selectExperimentSession(id)
      set({ experimentLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, experimentLoading: false })
    }
  },

  proposeExperiment: async (id) => {
    try {
      const proposal = await api.proposeExperiment(id)
      set({ experimentProposal: proposal })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  fetchExperimentResults: async (id) => {
    try {
      const result = await api.getExperimentResults(id)
      set({ experimentResultsTsv: result.tsv })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  selfModifyAgent: async (id, agentFile) => {
    try {
      set({ experimentLoading: true })
      await api.selfModifyAgent(id, agentFile)
      await get().selectExperimentSession(id)
      set({ experimentLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, experimentLoading: false })
    }
  },

  setExperimentProposal: (proposal) => set({ experimentProposal: proposal }),

  // ─── Notification Actions ────────────────────────────────────────────────────

  fetchNotifications: async () => {
    try {
      set({ notifLoading: true })
      const notifications = await api.getNotifications()
      set({ notifications, unreadCount: computeUnreadCount(notifications), notifLoading: false })
    } catch {
      set({ notifLoading: false })
    }
  },

  markNotificationRead: async (id: string) => {
    try {
      await api.markNotificationRead(id)
      const { notifications } = get()
      const updated = notifications.map((n) => (n.id === id ? { ...n, read: true } : n))
      set({ notifications: updated, unreadCount: computeUnreadCount(updated) })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  clearNotifications: async () => {
    try {
      await api.clearNotifications()
      set({ notifications: [], unreadCount: 0 })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },
}))
