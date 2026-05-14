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

export function Dashboard() {
  const navigate = useNavigate()
  const { sessions, loading, fetchSessions, health, fetchHealth, createSession } = useAppStore()

  const [projectPath, setProjectPath] = useState("")
  const [githubUrl, setGithubUrl] = useState("")
  const [goal, setGoal] = useState("")
  const [mode, setMode] = useState<SessionMode>(SessionMode.AUDIT)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const supportsDirectoryPicker = (() => {
    if (typeof window === "undefined" || typeof document === "undefined") return false
    const input = document.createElement("input")
    return "webkitdirectory" in input || "showDirectoryPicker" in window
  })()

  useEffect(() => {
    fetchSessions()
    fetchHealth()
  }, [])

  async function handleCreateSession() {
    const pathOrUrl = projectPath || githubUrl
    if (!pathOrUrl) return

    const id = await createSession(pathOrUrl, githubUrl, mode, goal)
    if (id) navigate(`/session/${id}`)
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">CodeAudit</h1>
            <p className="text-muted-foreground mt-1">AI-powered code audit system</p>
          </div>
          <div className="flex items-center gap-4">
            {health && (
              <Badge variant={health.status === "ok" ? "default" : "destructive"}>
                {health.status === "ok" ? "API Connected" : "API Disconnected"}
              </Badge>
            )}
            <span className="text-xs text-muted-foreground">v{health?.version}</span>
          </div>
        </div>

        {/* New Session */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>New Audit Session</CardTitle>
            <CardDescription>Point CodeAudit at a codebase to get started</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="projectPath">Local Project Path</Label>
                <div className="flex gap-2">
                  <Input
                    id="projectPath"
                    placeholder="/path/to/your/project"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    className="flex-1"
                  />
                  {supportsDirectoryPicker ? (
                    <>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        Browse
                      </Button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={(e) => {
                          const files = e.target.files
                          if (files && files.length > 0) {
                            const file = files[0]
                            const path = (file as any).path || file.name
                            setProjectPath(path)
                          }
                        }}
                        {...{ webkitdirectory: "", directory: "" }}
                        style={{ display: "none" }}
                      />
                    </>
                  ) : (
                    <p className="text-xs text-muted-foreground self-end pb-1">
                      Type the path manually (directory picker not supported in this browser)
                    </p>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="githubUrl">GitHub URL (optional)</Label>
                <Input
                  id="githubUrl"
                  placeholder="https://github.com/user/repo"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="goal">Goal (optional, for targeted audits)</Label>
              <Input
                id="goal"
                placeholder='e.g., "fix the React console errors" or "audit the auth flow"'
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Mode</Label>
              <div className="flex gap-2">
                {Object.values(SessionMode).map((m) => (
                  <Button
                    key={m}
                    variant={mode === m ? "default" : "outline"}
                    size="sm"
                    onClick={() => setMode(m)}
                  >
                    {m.replace(/_/g, " ")}
                  </Button>
                ))}
              </div>
            </div>
            <Button
              onClick={handleCreateSession}
              disabled={loading || (!projectPath && !githubUrl)}
            >
              {loading ? <Spinner className="mr-2" /> : null}
              Create Session
            </Button>
          </CardContent>
        </Card>

        {/* Live Agent Execution */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-sm">Agent Execution</CardTitle>
            <CardDescription>Live view of agent activity — start an audit to see it work</CardDescription>
          </CardHeader>
          <CardContent>
            <AgentExecGraph />
          </CardContent>
        </Card>

        {/* Sessions List */}
        <Card>
          <CardHeader>
            <CardTitle>Sessions</CardTitle>
            <CardDescription>Previous audit sessions</CardDescription>
          </CardHeader>
          <CardContent>
            {loading && sessions.length === 0 ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : sessions.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No sessions yet. Create one above to get started.
              </p>
            ) : (
              <div className="space-y-3">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-4 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => navigate(`/session/${session.id}`)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{session.project_name || "Unnamed Project"}</div>
                      <div className="text-sm text-muted-foreground truncate">
                        {session.project_path}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right text-sm">
                        <div>{session.findings_total} findings</div>
                        {session.findings_critical > 0 && (
                          <div className="text-red-500">{session.findings_critical} critical</div>
                        )}
                      </div>
                      <Badge variant="outline">{session.state}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
