import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { useAppStore } from "@/lib/store"
import { SessionMode } from "@/types"
import { AgentExecGraph } from "@/components/AgentExecGraph"
import {
  Rocket, Plus, History, Activity, ShieldCheck,
  Github, FolderOpen, ChevronRight, Sparkles, Zap
} from "lucide-react"
import { cn } from "@/lib/utils"

export function Dashboard() {
  const navigate = useNavigate()
  const { sessions, loading, fetchSessions, health, fetchHealth, createSession } = useAppStore()

  const [projectPath, setProjectPath] = useState("")
  const [githubUrl, setGithubUrl] = useState("")
  const [goal, setGoal] = useState("")
  const [mode, setMode] = useState<SessionMode>(SessionMode.AUDIT)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isElectron = !!(window as any).electronAPI

  const supportsDirectoryPicker = (() => {
    if (isElectron) return true
    if (typeof window === "undefined" || typeof document === "undefined") return false
    const input = document.createElement("input")
    return "webkitdirectory" in input || "showDirectoryPicker" in window
  })()

  useEffect(() => {
    fetchSessions()
    fetchHealth()
  }, [fetchSessions, fetchHealth])

  async function handleCreateSession() {
    const pathOrUrl = projectPath || githubUrl
    if (!pathOrUrl) return

    const id = await createSession(pathOrUrl, githubUrl, mode, goal)
    if (id) navigate(`/session/${id}`)
  }

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 swarm-grid p-6">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Top Navigation / Stats */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 bg-primary rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20">
              <Rocket className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Control Center</h1>
              <p className="text-slate-400 text-sm">Orchestrate your autonomous audit swarms</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right mr-4">
              <div className="text-[10px] uppercase font-bold text-slate-500 tracking-widest">System Health</div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="flex h-2 w-2 rounded-full bg-green-500" />
                <span className="text-sm font-medium">{health?.status === "ok" ? "Nominal" : "Degraded"}</span>
              </div>
            </div>
            <div className="h-10 w-px bg-slate-800" />
            <Button variant="outline" className="border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300">
              <Activity className="h-4 w-4 mr-2" />
              Metrics
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

          {/* Main Action Area */}
          <div className="lg:col-span-8 space-y-8">

            {/* New Session Card */}
            <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-md overflow-hidden relative group">
              <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
                <Plus className="h-24 w-24" />
              </div>
              <CardHeader className="pb-4">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className="bg-primary/10 text-primary border-primary/20 hover:bg-primary/20">Mission Start</Badge>
                </div>
                <CardTitle className="text-xl text-slate-100">Initialize New Audit</CardTitle>
                <CardDescription className="text-slate-200/60">Deploy agents to analyze and improve your codebase</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="projectPath" className="text-xs uppercase tracking-wider text-slate-500 font-bold">Local Repository</Label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <FolderOpen className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                        <Input
                          id="projectPath"
                          placeholder="/path/to/project"
                          value={projectPath}
                          onChange={(e) => setProjectPath(e.target.value)}
                          className="bg-slate-950/50 border-slate-800 pl-10 focus:ring-primary/20"
                        />
                      </div>
                      {supportsDirectoryPicker && (
                        <Button
                          variant="secondary"
                          size="sm"
                          className="bg-slate-800 hover:bg-slate-700 text-slate-200"
                          onClick={async () => {
                            if (isElectron) {
                              const path = await (window as any).electronAPI.selectDirectory()
                              if (path) setProjectPath(path)
                            } else {
                              fileInputRef.current?.click()
                            }
                          }}
                        >
                          Browse
                        </Button>
                      )}
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={(e) => {
                          const files = e.target.files
                          if (files && files.length > 0) {
                            const path = (files[0] as any).path || files[0].name
                            setProjectPath(path)
                          }
                        }}
                        {...{ webkitdirectory: "", directory: "" }}
                        style={{ display: "none" }}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="githubUrl" className="text-xs uppercase tracking-wider text-slate-500 font-bold">GitHub Source</Label>
                    <div className="relative">
                      <Github className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                      <Input
                        id="githubUrl"
                        placeholder="https://github.com/..."
                        value={githubUrl}
                        onChange={(e) => setGithubUrl(e.target.value)}
                        className="bg-slate-950/50 border-slate-800 pl-10 focus:ring-primary/20"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="goal" className="text-xs uppercase tracking-wider text-slate-500 font-bold">Primary Directive (Optional)</Label>
                  <div className="relative">
                    <Sparkles className="absolute left-3 top-2.5 h-4 w-4 text-primary/60" />
                    <Input
                      id="goal"
                      placeholder='e.g., "Deep audit of the auth flow" or "Performance optimization pass"'
                      value={goal}
                      onChange={(e) => setGoal(e.target.value)}
                      className="bg-slate-950/50 border-slate-800 pl-10 focus:ring-primary/20"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <div className="flex bg-slate-950/50 p-1 rounded-xl border border-slate-800">
                    {Object.values(SessionMode).map((m) => (
                      <button
                        key={m}
                        onClick={() => setMode(m)}
                        className={cn(
                          "px-4 py-1.5 rounded-lg text-xs font-bold transition-all uppercase tracking-wider",
                          mode === m
                            ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                            : "text-slate-500 hover:text-slate-300"
                        )}
                      >
                        {m.replace(/_/g, " ")}
                      </button>
                    ))}
                  </div>

                  <Button
                    size="lg"
                    onClick={handleCreateSession}
                    disabled={loading || (!projectPath && !githubUrl)}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 rounded-xl font-bold shadow-xl shadow-primary/20"
                  >
                    {loading ? <Spinner className="mr-2 h-4 w-4" /> : <Rocket className="mr-2 h-4 w-4" />}
                    DEPLOY AGENTS
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Execution Graph */}
            <Card className="bg-slate-900/40 border-slate-800 backdrop-blur-md">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div>
                  <CardTitle className="text-sm font-bold uppercase tracking-widest text-slate-400">Agent Live Stream</CardTitle>
                  <CardDescription>Real-time visual trace of agent thought processes</CardDescription>
                </div>
                <Badge variant="outline" className="bg-blue-500/5 text-blue-400 border-blue-500/20">
                  {sessions.length > 0 ? "STREAM ACTIVE" : "IDLE"}
                </Badge>
              </CardHeader>
              <CardContent className="h-64 flex items-center justify-center border-t border-slate-800/50 bg-slate-950/20">
                <AgentExecGraph />
              </CardContent>
            </Card>
          </div>

          {/* Sidebar Area */}
          <div className="lg:col-span-4 space-y-8">

            {/* Recent Sessions */}
            <div className="space-y-4">
              <div className="flex items-center justify-between px-2">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 flex items-center gap-2">
                  <History className="h-3 w-3" />
                  Mission History
                </h3>
                <Button variant="link" className="text-[10px] h-auto p-0 text-primary">View All</Button>
              </div>

              <div className="space-y-3">
                {loading && sessions.length === 0 ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-20 rounded-xl bg-slate-900/40 border border-slate-800 animate-pulse" />
                  ))
                ) : sessions.length === 0 ? (
                  <div className="p-8 text-center border border-dashed border-slate-800 rounded-2xl">
                    <p className="text-sm text-slate-500">No active missions</p>
                  </div>
                ) : (
                  sessions.slice(0, 5).map((session) => (
                    <div
                      key={session.id}
                      onClick={() => navigate(`/session/${session.id}`)}
                      className="group p-4 rounded-xl bg-slate-900/40 border border-slate-800 hover:border-primary/50 hover:bg-slate-800/40 transition-all cursor-pointer relative overflow-hidden"
                    >
                      <div className="absolute top-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <ChevronRight className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="h-10 w-10 shrink-0 rounded-lg bg-slate-950 flex items-center justify-center border border-slate-800">
                          {session.github_url ? <Github className="h-5 w-5 text-slate-400" /> : <FolderOpen className="h-5 w-5 text-slate-400" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-bold text-sm truncate group-hover:text-primary transition-colors">{session.project_name || "Unnamed Mission"}</div>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-[9px] py-0 px-1.5 border-slate-700 text-slate-500 uppercase">
                              {session.state}
                            </Badge>
                            <span className="text-[10px] text-slate-600 font-mono">{session.findings_total} FINDINGS</span>
                          </div>
                        </div>
                      </div>
                      {session.findings_critical > 0 && (
                        <div className="mt-3 h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-red-500 w-1/3 shadow-[0_0_8px_rgba(239,68,68,0.5)]" />
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Quick Insights */}
            <Card className="bg-slate-900/40 border-slate-800">
               <CardHeader className="pb-2">
                <CardTitle className="text-xs font-bold uppercase tracking-widest text-slate-400">Overview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                 <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                    <div className="flex items-center gap-3">
                      <ShieldCheck className="h-4 w-4 text-green-500" />
                      <span className="text-xs font-medium">Security Index</span>
                    </div>
                    <span className="font-mono text-xs font-bold text-green-500">88%</span>
                 </div>
                 <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                    <div className="flex items-center gap-3">
                      <Zap className="h-4 w-4 text-yellow-500" />
                      <span className="text-xs font-medium">Auto-Fix Velocity</span>
                    </div>
                    <span className="font-mono text-xs font-bold text-yellow-500">12/hr</span>
                 </div>
              </CardContent>
            </Card>

          </div>

        </div>

      </div>
    </div>
  )
}
