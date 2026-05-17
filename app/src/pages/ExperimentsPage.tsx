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
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-white uppercase italic flex items-center gap-3">
              <FlaskConical className="h-10 w-10 text-violet-500" />
              Evolution Lab
            </h1>
            <p className="text-slate-400 mt-1 font-mono text-sm uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-violet-500 animate-pulse" />
              Autonomous Self-Modification & Optimization Loop
            </p>
          </div>
          {view === "detail" && (
            <Button
              variant="ghost"
              onClick={() => { setView("list"); setExperimentProposal(null) }}
              className="border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-900 uppercase text-[10px] font-bold tracking-widest"
            >
              Back to Archive
            </Button>
          )}
        </div>

        {view === "list" ? (
          <>
            <Card className="mb-8 glass border-slate-800 bg-slate-900/40">
              <CardHeader>
                <CardTitle className="text-white uppercase tracking-tight font-bold">Initialize Neural Cycle</CardTitle>
                <CardDescription className="text-slate-500 font-mono text-xs uppercase italic">Deploy an autonomous researcher to optimize a target environment</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="expProjectPath" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Project Topology Root</Label>
                  <Input
                    id="expProjectPath"
                    placeholder="/absolute/path/to/project"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    className="bg-slate-950 border-slate-800 text-violet-100 font-mono text-sm focus:ring-violet-500/50"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="targetFile" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Target Module</Label>
                    <Input
                      id="targetFile"
                      placeholder="e.g., core/engine.py"
                      value={targetFile}
                      onChange={(e) => setTargetFile(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs focus:ring-violet-500/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tag" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Experiment Tag</Label>
                    <Input
                      id="tag"
                      placeholder="e.g., optimization-v1"
                      value={tag}
                      onChange={(e) => setTag(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs focus:ring-violet-500/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timeBudget" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Compute Budget (s)</Label>
                    <Input
                      id="timeBudget"
                      type="number"
                      value={timeBudget}
                      onChange={(e) => setTimeBudget(Number(e.target.value))}
                      className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs focus:ring-violet-500/50"
                    />
                  </div>
                </div>
                <Button
                  onClick={handleCreate}
                  disabled={!projectPath || experimentLoading}
                  className="w-full bg-violet-600 hover:bg-violet-500 text-white font-black uppercase tracking-[0.2em] py-6 shadow-[0_0_20px_rgba(139,92,246,0.2)]"
                >
                  {experimentLoading ? <Spinner className="mr-2" /> : <Plus className="mr-2 h-4 w-4" />}
                  INITIALIZE SESSION
                </Button>
              </CardContent>
            </Card>

            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader>
                <CardTitle className="text-white uppercase tracking-tight font-bold">Historical Archive</CardTitle>
                <CardDescription className="text-slate-500 font-mono text-xs uppercase italic">Stored evolutionary cycles</CardDescription>
              </CardHeader>
              <CardContent>
                {experimentLoading && experimentSessions.length === 0 ? (
                  <div className="flex justify-center py-16"><Spinner /></div>
                ) : experimentSessions.length === 0 ? (
                  <div className="text-center py-20 bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
                    <p className="text-slate-600 font-mono text-[10px] uppercase tracking-widest italic">Archive Empty</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {experimentSessions.map((s) => (
                      <div
                        key={s.id}
                        className="group flex flex-col p-4 bg-slate-950/60 border border-slate-800 rounded-xl cursor-pointer hover:border-violet-500/50 hover:bg-slate-900/60 transition-all duration-300"
                        onClick={() => { selectExperimentSession(s.id); setView("detail") }}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="font-bold text-slate-200 group-hover:text-white uppercase tracking-wide text-xs truncate flex items-center gap-2">
                            <FlaskConical className="h-3 w-3 text-violet-400" />
                            {s.tag || "UNTITLED_CYCLE"}
                            {s.is_running && <div className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-pulse" />}
                          </div>
                          <Badge className={s.is_running ? "bg-violet-500/10 text-violet-400" : "bg-slate-900 text-slate-500 border-none"}>
                            {s.is_running ? "ACTIVE" : "COMPLETED"}
                          </Badge>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono truncate mb-4 opacity-70">
                          {s.project_path}
                        </div>
                        <div className="flex items-center justify-between mt-auto pt-3 border-t border-slate-800/50">
                          <div className="text-[9px] font-bold text-slate-600 uppercase">
                            RUNS: <span className="text-slate-300">{s.total_runs}</span>
                          </div>
                          <div className={`text-[11px] font-mono font-black ${s.best_bpb < Infinity ? "text-emerald-400" : "text-slate-700"}`}>
                            BEST: {formatBpb(s.best_bpb)}
                          </div>
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
                  <Card className="glass border-slate-800 bg-slate-900/40">
                    <CardHeader className="pb-4">
                      <CardTitle className="flex items-center justify-between text-white uppercase font-black italic tracking-tight">
                        <span>SESSION: {currentExperiment.tag || currentExperiment.id.slice(0, 8)}</span>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => { deleteExperimentSession(currentExperiment.id); setView("list") }}
                            className="text-slate-600 hover:text-red-400 hover:bg-red-500/10 border border-slate-800 hover:border-red-500/30"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </CardTitle>
                      <CardDescription className="font-mono text-[10px] uppercase text-slate-500">
                        BRANCH: {currentExperiment.branch} &middot;{" "}
                        BUDGET: {currentExperiment.time_budget}S &middot;{" "}
                        OPS: {currentExperiment.total_runs}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-center">
                          <div className="text-2xl font-mono font-black text-emerald-400">
                            {formatBpb(currentExperiment.best_bpb)}
                          </div>
                          <div className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Best Val_BPB</div>
                        </div>
                        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-center">
                          <div className="text-2xl font-mono font-black text-slate-200">
                            {currentExperiment.total_runs}
                          </div>
                          <div className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Total Cycles</div>
                        </div>
                        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-center">
                          <div className="text-2xl font-mono font-black text-violet-400">
                            {currentExperiment.experiments.filter(e => e.status === "kept").length}
                          </div>
                          <div className-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Mutations Kept</div>
                        </div>
                      </div>

                      <div className="flex gap-3">
                        <Button
                          onClick={handleEstablishBaseline}
                          disabled={experimentLoading}
                          className="flex-1 bg-slate-900 border border-slate-800 hover:border-violet-500/50 text-slate-300 font-bold uppercase text-[10px] tracking-widest py-5"
                        >
                          <Target className="mr-2 h-4 w-4 text-violet-400" />
                          ESTABLISH BASELINE
                        </Button>
                        <Button
                          onClick={handlePropose}
                          variant="secondary"
                          disabled={experimentLoading}
                          className="flex-1 bg-violet-600 hover:bg-violet-500 text-white font-bold uppercase text-[10px] tracking-widest py-5"
                        >
                          <Lightbulb className="mr-2 h-4 w-4" />
                          PROPOSE MUTATION
                        </Button>
                      </div>

                      {experimentProposal && (
                        <Card className="border-violet-500/30 bg-violet-500/5 relative overflow-hidden">
                          <div className="absolute top-0 right-0 p-2 text-[10px] font-mono text-violet-500/50 uppercase font-black italic">Proposed Node</div>
                          <CardHeader className="py-4">
                            <CardTitle className="text-xs font-bold text-violet-300 uppercase tracking-widest">
                              HYPOTHESIS: {experimentProposal.description}
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4 text-xs">
                            <div className="bg-slate-950/40 p-3 rounded border border-violet-500/10">
                              <span className="text-[10px] font-bold text-slate-600 uppercase block mb-1">Rationale</span>
                              <p className="text-slate-400 leading-relaxed italic">{experimentProposal.rationale}</p>
                            </div>
                            {experimentProposal.code_change && (
                              <div className="space-y-1">
                                <span className="text-[10px] font-bold text-slate-600 uppercase block ml-1">Structural Change</span>
                                <pre className="text-[10px] bg-slate-950 border border-slate-800 p-3 rounded-lg overflow-auto max-h-32 text-violet-100/70 font-mono">
                                  {experimentProposal.code_change}
                                </pre>
                              </div>
                            )}
                            <div className="flex gap-2 pt-2">
                              <Button
                                size="sm"
                                onClick={() => {
                                  setExpDescription(experimentProposal.description)
                                  setCodeChange(experimentProposal.code_change)
                                  setExperimentProposal(null)
                                }}
                                className="bg-violet-600 hover:bg-violet-500 text-white font-bold uppercase text-[9px] tracking-widest h-8"
                              >
                                EXECUTE PROTOCOL
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => setExperimentProposal(null)}
                                className="text-slate-600 hover:text-slate-400 uppercase text-[9px] font-bold h-8"
                              >
                                DISCARD
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </CardContent>
                  </Card>

                  <Card className="glass border-slate-800 bg-slate-900/40">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-white uppercase font-bold tracking-tight flex items-center gap-2">
                        <Play className="h-4 w-4 text-emerald-400" />
                        Manual Injection
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-1.5">
                        <Label htmlFor="expDesc" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Directive</Label>
                        <Input
                          id="expDesc"
                          placeholder="e.g., increase hidden layer dimension to 2048"
                          value={expDescription}
                          onChange={(e) => setExpDescription(e.target.value)}
                          className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="codeChange" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Modified Structure (Optional)</Label>
                        <Textarea
                          id="codeChange"
                          placeholder="Enter RAW patch or transformation logic..."
                          value={codeChange}
                          onChange={(e) => setCodeChange(e.target.value)}
                          className="min-h-[100px] bg-slate-950 border-slate-800 text-slate-400 font-mono text-xs resize-none"
                        />
                      </div>
                      <Button
                        onClick={handleRunExperiment}
                        disabled={!expDescription || experimentLoading}
                        className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold uppercase tracking-widest text-[10px] py-4"
                      >
                        {experimentLoading ? <Spinner className="mr-2" /> : <Play className="mr-2 h-4 w-4" />}
                        ENGAGE MANUAL CYCLE
                      </Button>
                    </CardContent>
                  </Card>

                  <Card className="glass border-slate-800 bg-slate-900/40">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-white uppercase font-bold tracking-tight flex items-center gap-2">
                        <RotateCcw className="h-4 w-4 text-blue-400" />
                        Neural Feedback Loop
                      </CardTitle>
                      <CardDescription className="text-slate-500 font-mono text-[10px] uppercase italic">Allow the agent to improve its own architectural source</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-1.5">
                        <Label htmlFor="agentFile" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Agent Neural Target (Relative Path)</Label>
                        <Input
                          id="agentFile"
                          placeholder="e.g., agents/neural_controller.py"
                          value={agentFile}
                          onChange={(e) => setAgentFile(e.target.value)}
                          className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs"
                        />
                      </div>
                      <Button
                        variant="secondary"
                        onClick={() => selfModifyAgent(currentExperiment.id, agentFile)}
                        disabled={!agentFile || experimentLoading}
                        className="w-full bg-blue-600/10 border border-blue-500/30 text-blue-400 hover:bg-blue-600/20 font-bold uppercase tracking-widest text-[10px] py-4"
                      >
                        <RotateCcw className="mr-2 h-4 w-4" />
                        ENGAGE SELF-MODIFICATION
                      </Button>
                    </CardContent>
                  </Card>

                  <Card className="glass border-slate-800 bg-slate-900/40">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-white uppercase font-bold tracking-tight flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-violet-400" />
                        Live Mutation Stream
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {currentExperiment.experiments.length === 0 ? (
                        <div className="text-center py-12 bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
                          <p className="text-slate-600 font-mono text-[10px] uppercase tracking-widest italic tracking-tighter">Monitoring neural activity...</p>
                        </div>
                      ) : (
                        <div className="space-y-2 max-h-[400px] overflow-y-auto scrollbar-hide pr-2">
                          {[...currentExperiment.experiments].reverse().map((exp) => (
                            <div
                              key={exp.id}
                              className="group flex items-center justify-between p-3 bg-slate-950/40 border border-slate-800/50 rounded-lg hover:border-violet-500/30 hover:bg-slate-900/50 transition-all duration-200"
                            >
                              <div className="flex-1 min-w-0 pr-4">
                                <span className="font-sans text-[11px] text-slate-300 group-hover:text-white transition-colors truncate block">{exp.description}</span>
                                <div className="flex items-center gap-3 mt-1.5">
                                  <span className="text-[9px] font-mono text-slate-600 uppercase">
                                    LATENCY: {exp.duration_seconds.toFixed(1)}S
                                  </span>
                                  <span className="w-1 h-1 rounded-full bg-slate-800" />
                                  <span className="text-[9px] font-mono text-slate-600 uppercase">
                                    {exp.created_at?.slice(11, 19)}
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center gap-4 shrink-0">
                                <div className="text-right">
                                  <div className="text-[8px] font-bold text-slate-600 uppercase">VAL_BPB</div>
                                  <div className="font-mono text-xs text-emerald-400 font-bold">{exp.val_bpb.toFixed(6)}</div>
                                </div>
                                <Badge className={`text-[9px] font-bold uppercase px-2 py-0.5 border-none ${
                                  exp.status === "kept" ? "bg-emerald-500/10 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.1)]" :
                                  exp.status === "discarded" ? "bg-slate-800 text-slate-500" :
                                  exp.status === "crashed" ? "bg-red-500/10 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.1)]" : "bg-slate-950 text-slate-600"
                                }`}>
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
                  <Card className="glass border-slate-800 bg-slate-900/40">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-xs font-bold text-slate-200 uppercase tracking-widest">Environment Target</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                        <p className="text-[11px] font-mono text-violet-300 break-all leading-relaxed">
                          {currentExperiment.target_file || "// NULL_TARGET_DEFINED"}
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
                    <CardHeader className="pb-3 flex flex-row items-center justify-between">
                      <CardTitle className="text-xs font-bold text-slate-200 uppercase tracking-widest">TSV Telemetry</CardTitle>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-slate-500 hover:text-violet-400 hover:bg-violet-500/10"
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
                      <div className="relative group">
                        <pre className="text-[9px] font-mono bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-500 overflow-auto max-h-[300px] whitespace-pre scrollbar-hide">
                          {experimentResultsTsv || "// NO_RESULTS_SYNCHRONIZED"}
                        </pre>
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-slate-950/20 pointer-events-none group-hover:opacity-0 transition-opacity" />
                      </div>
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
