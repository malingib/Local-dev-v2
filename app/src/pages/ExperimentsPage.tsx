import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { useAppStore } from "@/lib/store"
import {
  FlaskConical, Play, Plus, Trash2, Download, RotateCcw,
  Lightbulb, FileCode, Target, BarChart3,
} from "lucide-react"

export function ExperimentsPage() {
  const {
    experimentSessions, currentExperiment, experimentProposal,
    experimentResultsTsv, experimentLoading,
    fetchExperimentSessions, createExperimentSession,
    selectExperimentSession, deleteExperimentSession,
    establishBaseline, runExperiment, proposeExperiment,
    selfModifyAgent,
    setExperimentProposal,
  } = useAppStore()

  const [projectPath, setProjectPath] = useState("")
  const [targetFile, setTargetFile] = useState("")
  const [tag, setTag] = useState("")
  const [timeBudget, setTimeBudget] = useState(300)
  const [expDescription, setExpDescription] = useState("")
  const [codeChange, setCodeChange] = useState("")
  const [agentFile, setAgentFile] = useState("")
  const [view, setView] = useState<"list" | "detail">("list")

  useEffect(() => {
    fetchExperimentSessions()
  }, [fetchExperimentSessions])

  async function handleCreate() {
    if (!projectPath) return
    const id = await createExperimentSession({
      project_path: projectPath,
      target_file: targetFile || undefined,
      tag: tag || undefined,
      time_budget: timeBudget,
    })
    if (id) {
      await selectExperimentSession(id)
      setView("detail")
    }
  }

  async function handlePropose() {
    if (!currentExperiment) return
    await proposeExperiment(currentExperiment.id)
  }

  async function handleRunExperiment() {
    if (!currentExperiment || !expDescription) return
    await runExperiment(currentExperiment.id, expDescription, codeChange)
    setExpDescription("")
    setCodeChange("")
  }

  async function handleEstablishBaseline() {
    if (!currentExperiment) return
    await establishBaseline(currentExperiment.id)
  }

  function formatBpb(bpb: number) {
    return bpb === Infinity ? "—" : bpb.toFixed(6)
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <FlaskConical className="h-7 w-7" />
              AutoResearch
            </h1>
            <p className="text-muted-foreground mt-1">
              Autonomous experiment loop — inspired by karpathy/autoresearch
            </p>
          </div>
          {view === "detail" && (
            <Button variant="outline" onClick={() => { setView("list"); setExperimentProposal(null) }}>
              Back to Sessions
            </Button>
          )}
        </div>

        {view === "list" ? (
          <>
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>New Experiment Session</CardTitle>
                <CardDescription>Set up an autonomous experiment loop</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="expProjectPath">Project Path</Label>
                  <Input
                    id="expProjectPath"
                    placeholder="/path/to/your/project"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="targetFile">Target File</Label>
                    <Input
                      id="targetFile"
                      placeholder="e.g., train.py"
                      value={targetFile}
                      onChange={(e) => setTargetFile(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tag">Tag</Label>
                    <Input
                      id="tag"
                      placeholder="e.g., may13"
                      value={tag}
                      onChange={(e) => setTag(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timeBudget">Time Budget (s)</Label>
                    <Input
                      id="timeBudget"
                      type="number"
                      value={timeBudget}
                      onChange={(e) => setTimeBudget(Number(e.target.value))}
                    />
                  </div>
                </div>
                <Button onClick={handleCreate} disabled={!projectPath || experimentLoading}>
                  {experimentLoading ? <Spinner className="mr-2" /> : <Plus className="mr-2 h-4 w-4" />}
                  Create Session
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Experiment Sessions</CardTitle>
                <CardDescription>Your autonomous research sessions</CardDescription>
              </CardHeader>
              <CardContent>
                {experimentLoading && experimentSessions.length === 0 ? (
                  <div className="flex justify-center py-8"><Spinner /></div>
                ) : experimentSessions.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    No experiment sessions yet. Create one above.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {experimentSessions.map((s) => (
                      <div
                        key={s.id}
                        className="flex items-center justify-between p-4 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => { selectExperimentSession(s.id); setView("detail") }}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="font-medium flex items-center gap-2">
                            {s.tag || "untagged"}
                            {s.is_running && <Spinner className="h-3 w-3" />}
                          </div>
                          <div className="text-sm text-muted-foreground truncate">
                            {s.project_path} {s.target_file && `→ ${s.target_file}`}
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="text-right">
                            <div>{s.total_runs} runs</div>
                            <div className={s.best_bpb < Infinity ? "text-green-500" : ""}>
                              best: {formatBpb(s.best_bpb)}
                            </div>
                          </div>
                          <Badge variant={s.is_running ? "default" : "outline"}>
                            {s.is_running ? "running" : `${s.time_budget}s`}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : (
          <>
            {currentExperiment && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Session: {currentExperiment.tag || currentExperiment.id}</span>
                        <div className="flex gap-2">
                          <Button
                            variant="outline" size="sm"
                            onClick={() => { deleteExperimentSession(currentExperiment.id); setView("list") }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardTitle>
                      <CardDescription>
                        Branch: {currentExperiment.branch} &middot;{" "}
                        Time budget: {currentExperiment.time_budget}s &middot;{" "}
                        Runs: {currentExperiment.total_runs}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="border rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold text-green-500">
                            {formatBpb(currentExperiment.best_bpb)}
                          </div>
                          <div className="text-xs text-muted-foreground">Best val_bpb</div>
                        </div>
                        <div className="border rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold">
                            {currentExperiment.total_runs}
                          </div>
                          <div className="text-xs text-muted-foreground">Total Runs</div>
                        </div>
                        <div className="border rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold">
                            {currentExperiment.experiments.filter(e => e.status === "kept").length}
                          </div>
                          <div className="text-xs text-muted-foreground">Kept</div>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button onClick={handleEstablishBaseline} disabled={experimentLoading}>
                          <Target className="mr-2 h-4 w-4" />
                          Establish Baseline
                        </Button>
                        <Button onClick={handlePropose} variant="secondary" disabled={experimentLoading}>
                          <Lightbulb className="mr-2 h-4 w-4" />
                          Propose Experiment
                        </Button>
                      </div>

                      {experimentProposal && (
                        <Card className="border-primary/20 bg-primary/5">
                          <CardHeader className="py-3">
                            <CardTitle className="text-sm font-medium">
                              Proposed: {experimentProposal.description}
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-2 text-sm">
                            <p><span className="text-muted-foreground">Rationale:</span> {experimentProposal.rationale}</p>
                            {experimentProposal.code_change && (
                              <div>
                                <span className="text-muted-foreground">Change:</span>
                                <pre className="mt-1 text-xs bg-muted p-2 rounded overflow-auto max-h-20">
                                  {experimentProposal.code_change}
                                </pre>
                              </div>
                            )}
                            <div className="flex gap-2 pt-2">
                              <Button size="sm" onClick={() => {
                                setExpDescription(experimentProposal.description)
                                setCodeChange(experimentProposal.code_change)
                                setExperimentProposal(null)
                              }}>
                                Use This
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => setExperimentProposal(null)}>
                                Dismiss
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Run Experiment</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="expDesc">Description</Label>
                        <Input
                          id="expDesc"
                          placeholder="e.g., increase learning rate to 0.04"
                          value={expDescription}
                          onChange={(e) => setExpDescription(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="codeChange">Code Change (optional)</Label>
                        <Textarea
                          id="codeChange"
                          placeholder="Describe the code change or what to modify..."
                          value={codeChange}
                          onChange={(e) => setCodeChange(e.target.value)}
                          className="min-h-[80px]"
                        />
                      </div>
                      <Button
                        onClick={handleRunExperiment}
                        disabled={!expDescription || experimentLoading}
                      >
                        {experimentLoading ? <Spinner className="mr-2" /> : <Play className="mr-2 h-4 w-4" />}
                        Run Experiment
                      </Button>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        <FileCode className="h-4 w-4" />
                        Self-Modify Agent
                      </CardTitle>
                      <CardDescription>Let the agent improve its own source code</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="agentFile">Agent File Path (relative to project)</Label>
                        <Input
                          id="agentFile"
                          placeholder="e.g., agents/base_agent.py"
                          value={agentFile}
                          onChange={(e) => setAgentFile(e.target.value)}
                        />
                      </div>
                      <Button
                        variant="secondary"
                        onClick={() => selfModifyAgent(currentExperiment.id, agentFile)}
                        disabled={!agentFile || experimentLoading}
                      >
                        <RotateCcw className="mr-2 h-4 w-4" />
                        Self-Modify
                      </Button>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        <BarChart3 className="h-4 w-4" />
                        Experiment Log
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {currentExperiment.experiments.length === 0 ? (
                        <p className="text-muted-foreground text-sm">No experiments yet</p>
                      ) : (
                        <div className="space-y-2 max-h-80 overflow-y-auto">
                          {[...currentExperiment.experiments].reverse().map((exp) => (
                            <div
                              key={exp.id}
                              className="flex items-center justify-between text-sm border-b pb-2 last:border-0"
                            >
                              <div className="flex-1 min-w-0">
                                <span className="truncate block">{exp.description}</span>
                                <span className="text-xs text-muted-foreground">
                                  {exp.duration_seconds.toFixed(1)}s &middot; {exp.created_at?.slice(0, 19)?.replace("T", " ")}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                <span className="font-mono text-xs">{exp.val_bpb.toFixed(6)}</span>
                                <Badge variant={
                                  exp.status === "kept" ? "default" :
                                  exp.status === "discarded" ? "secondary" :
                                  exp.status === "crashed" ? "destructive" : "outline"
                                } className="text-[10px] px-1.5">
                                  {exp.status}
                                </Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Target File</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm font-mono">{currentExperiment.target_file || "N/A"}</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle className="text-sm">Results TSV</CardTitle>
                      <Button
                        variant="ghost" size="sm"
                        onClick={() => {
                          const blob = new Blob([experimentResultsTsv], { type: "text/tab-separated-values" })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement("a")
                          a.href = url; a.download = `results_${currentExperiment.tag}.tsv`
                          a.click(); URL.revokeObjectURL(url)
                        }}
                        disabled={!experimentResultsTsv}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <pre className="text-[10px] font-mono bg-muted p-2 rounded overflow-auto max-h-60 whitespace-pre">
                        {experimentResultsTsv || "No results yet"}
                      </pre>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
