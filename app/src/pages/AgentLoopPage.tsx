import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import * as api from "@/lib/api"
import {
  RotateCcw, Activity, TrendingUp, Lightbulb, CheckCircle2,
  XCircle, Brain, Zap, Target, Terminal, Search, Layers, Cpu
} from "lucide-react"

export function AgentLoopPage() {
  const [sessionId, setSessionId] = useState("")
  const [targetFile, setTargetFile] = useState("")
  const [iterations, setIterations] = useState(3)
  const [traces, setTraces] = useState<Array<Record<string, unknown>>>([])
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null)
  const [improvements, setImprovements] = useState<Array<Record<string, unknown>>>([])
  const [benchmarks, setBenchmarks] = useState<Array<Record<string, unknown>>>([])
  const [loopResults, setLoopResults] = useState<Array<Record<string, unknown>> | null>(null)
  const [loading, setLoading] = useState(false)
  const [loopLoading, setLoopLoading] = useState(false)

  async function handleAnalyze() {
    setLoading(true)
    try {
      const [a, t, imps, bench] = await Promise.all([
        api.analyzeAgentTraces(sessionId),
        api.getAgentTraces(sessionId, 50),
        api.getAgentImprovements(sessionId),
        api.getLoopBenchmarks(),
      ])
      setAnalysis(a)
      setTraces(t)
      setImprovements(imps)
      setBenchmarks(bench)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function handleGenerateImprovements() {
    setLoading(true)
    try {
      const imps = await api.generateAgentImprovements(sessionId)
      setImprovements(imps)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function handleApply(impId: number) {
    setLoading(true)
    await api.applyAgentImprovement(impId, targetFile)
    await handleAnalyze()
    setLoading(false)
  }

  async function handleRunLoop() {
    setLoopLoading(true)
    try {
      const results = await api.runImprovementLoop(sessionId, targetFile, iterations)
      setLoopResults(results)
      await handleAnalyze()
    } catch (e) { console.error(e) }
    setLoopLoading(false)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl shadow-inner">
              <Brain className="h-8 w-8 text-white animate-pulse" />
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tighter text-white uppercase italic leading-none">Recursive Lab</h1>
              <p className="text-slate-500 mt-1 font-mono text-[10px] uppercase tracking-[0.3em]">HALO-Style Self-Improvement Loop & Trace Matrix</p>
            </div>
          </div>
          <div className="hidden lg:flex items-center gap-6">
            <div className="text-right">
              <div className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">Mutation Depth</div>
              <div className="text-xs font-mono text-emerald-500">LEVEL_04_SENTIENCE</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-8 space-y-8">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-4">
                <CardTitle className="text-white uppercase font-black text-lg tracking-tight flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-slate-400" />
                  Loop configuration
                </CardTitle>
                <CardDescription className="font-mono text-[10px] uppercase text-slate-500">Parameters for the autonomous evolution sequence</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="aloopSession" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Context ID</Label>
                    <Input
                      id="aloopSession"
                      placeholder="SCAN_SESSION_ID..."
                      value={sessionId}
                      onChange={(e) => setSessionId(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-[10px] font-mono uppercase h-10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="aloopTarget" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Target Module</Label>
                    <Input
                      id="aloopTarget"
                      placeholder="path/to/source.ts"
                      value={targetFile}
                      onChange={(e) => setTargetFile(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-[10px] font-mono h-10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="aloopIters" className="text-[10px] font-bold text-slate-500 uppercase ml-1">Evo Cycles</Label>
                    <Input
                      id="aloopIters"
                      type="number"
                      value={iterations}
                      onChange={(e) => setIterations(Number(e.target.value))}
                      className="bg-slate-950 border-slate-800 text-[10px] font-mono h-10"
                    />
                  </div>
                </div>
                <div className="flex gap-3 flex-wrap pt-2">
                  <Button
                    onClick={handleAnalyze}
                    disabled={loading}
                    className="flex-1 bg-slate-900 border border-slate-800 hover:border-slate-500/50 text-slate-200 font-black uppercase text-[10px] tracking-widest h-12"
                  >
                    {loading ? <Spinner className="mr-2" /> : <Search className="mr-2 h-4 w-4" />}
                    PROBE TRACES
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleGenerateImprovements}
                    disabled={loading}
                    className="flex-1 border-slate-800 bg-slate-950/40 text-slate-400 hover:text-white uppercase text-[10px] font-black tracking-widest h-12"
                  >
                    <Lightbulb className="mr-2 h-4 w-4" />
                    GENERATE FIXES
                  </Button>
                  <Button
                    onClick={handleRunLoop}
                    disabled={loopLoading}
                    className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-black uppercase text-[10px] tracking-widest h-12 shadow-lg shadow-blue-900/20"
                  >
                    {loopLoading ? <Spinner className="mr-2" /> : <RotateCcw className="mr-2 h-4 w-4" />}
                    EXECUTE FULL EVOLUTION
                  </Button>
                </div>
              </CardContent>
            </Card>

            {analysis && !(analysis as any).error && (
              <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
                <CardHeader className="pb-2 border-b border-slate-800/50 mb-6 bg-slate-950/20">
                  <CardTitle className="text-white uppercase font-black text-sm tracking-tight flex items-center gap-2">
                    <Activity className="h-4 w-4 text-emerald-500" />
                    Telemetry Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    {[
                      { label: "Traces Analyzed", value: (analysis as any).total, color: "text-white" },
                      { label: "Success Rate", value: `${(analysis as any).success_rate}%`, color: "text-emerald-500" },
                      { label: "Critical Failures", value: (analysis as any).failures, color: "text-rose-500" },
                      { label: "Avg Latency", value: `${Math.round((analysis as any).avg_duration_ms)}ms`, color: "text-blue-400" },
                    ].map((stat, i) => (
                      <div key={i} className="bg-slate-950/60 rounded-xl border border-slate-800 p-4 text-center">
                        <div className={`text-2xl font-black ${stat.color} tracking-tighter`}>{stat.value}</div>
                        <div className="text-[9px] text-slate-600 font-bold uppercase tracking-widest mt-1">{stat.label}</div>
                      </div>
                    ))}
                  </div>

                  {analysis && (analysis as any).agents && (
                    <div className="space-y-3">
                      <div className="text-[9px] font-bold text-slate-600 uppercase tracking-widest ml-1">Agent Payload Distribution</div>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries((analysis as any).agents as Record<string, number>).map(([agent, count]) => (
                          <div key={agent} className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded flex items-center gap-3">
                            <span className="text-[10px] font-mono text-slate-300 uppercase">{agent}</span>
                            <span className="text-[10px] font-black text-blue-500">{String(count)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {improvements.length > 0 && (
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader>
                  <CardTitle className="text-white uppercase font-black text-lg tracking-tight flex items-center gap-2">
                    <Zap className="h-4 w-4 text-amber-500" />
                    Suggested Mutations ({improvements.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {improvements.map((imp: any, i) => (
                    <div key={i} className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 group hover:border-slate-700 transition-all">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <Badge className={`${imp.impact_score > 7 ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-slate-800 text-slate-500"} text-[8px] font-mono h-4`}>
                            {imp.category.toUpperCase()}
                          </Badge>
                          <span className="font-bold text-xs text-slate-200 uppercase tracking-tight">{imp.description}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-[9px] font-mono text-slate-600 uppercase">Impact: {imp.impact_score}/10</span>
                          {imp.applied ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : null}
                        </div>
                      </div>
                      <p className="text-[11px] text-slate-400 font-mono leading-relaxed mb-4 italic">"{imp.suggestion}"</p>
                      {!imp.applied && (
                        <Button
                          size="sm"
                          onClick={() => handleApply(imp.id)}
                          disabled={loading}
                          className="bg-slate-200 hover:bg-white text-slate-950 font-black uppercase text-[9px] tracking-widest px-6"
                        >
                          APPLY_PATCH
                        </Button>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {loopResults && (
              <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
                <div className="h-1 bg-gradient-to-r from-blue-500 to-indigo-500" />
                <CardHeader>
                  <CardTitle className="text-white uppercase font-black text-lg tracking-tight flex items-center gap-2">
                    <Target className="h-4 w-4 text-blue-500" />
                    Evolution Log
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {loopResults.map((r: any, i) => (
                    <div key={i} className="bg-slate-950/40 border border-slate-800 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="text-[11px] font-black text-white uppercase tracking-[0.2em]">CYCLE_{String(r.iteration).padStart(2, '0')}</div>
                        <Badge variant="outline" className="text-[8px] font-mono text-slate-500 border-slate-800">
                          {r.improvements_found} MUTATIONS_DETECTED
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        {r.applied && r.applied.map((a: any, j: number) => (
                          <div key={j} className="text-[10px] font-mono flex items-center gap-3 p-2 bg-black/20 rounded border border-slate-900">
                            {a.status === "applied" ? (
                              <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                            ) : (
                              <XCircle className="h-3 w-3 text-rose-500" />
                            )}
                            <span className="text-slate-400 uppercase">{a.status}:</span>
                            <span className="text-slate-200 truncate">{a.suggestion}</span>
                          </div>
                        ))}
                      </div>

                      {r.benchmark && r.benchmark.metrics && (
                        <div className="mt-4 grid grid-cols-2 gap-4 border-t border-slate-800 pt-4">
                          <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">Baseline_Latency: {Math.round(r.benchmark.metrics.avg_duration_ms)}ms</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">Success_Delta: {Math.round(r.benchmark.metrics.success_rate)}%</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          <div className="lg:col-span-4 space-y-8">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3 border-b border-slate-800/50">
                <CardTitle className="text-[11px] font-black uppercase text-slate-500 tracking-[0.2em] flex items-center justify-between">
                  Mission Traces <span className="text-slate-700 font-mono text-[9px]">{traces.length}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {traces.length === 0 ? (
                  <div className="py-12 text-center">
                    <span className="text-[10px] font-mono text-slate-700 uppercase italic">NO_TELEMETRY_LOGGED</span>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-800/50 max-h-[600px] overflow-y-auto custom-scrollbar">
                    {traces.slice(0, 30).map((t: any) => (
                      <div key={t.id} className="p-3 flex items-center gap-4 group hover:bg-slate-800/20 transition-all">
                        {t.success ? (
                          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                        ) : (
                          <div className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="text-[10px] font-bold text-slate-300 uppercase truncate tracking-tight">{t.action || t.tool || "NULL_OP"}</div>
                          <div className="text-[8px] font-mono text-slate-600 mt-0.5">{t.id} &middot; {t.duration_ms}ms</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {benchmarks.length > 0 && (
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-3 border-b border-slate-800/50">
                  <CardTitle className="text-[11px] font-black uppercase text-slate-500 tracking-[0.2em] flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" /> Global Benchmarks
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="space-y-4">
                    {benchmarks.slice(0, 10).map((b: any) => (
                      <div key={b.id} className="group">
                        <div className="flex justify-between items-center mb-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">{b.metric_name}</span>
                          <span className={`text-[10px] font-mono font-black ${b.improvement_pct > 0 ? "text-emerald-500" : "text-rose-500"}`}>
                            {b.improvement_pct > 0 ? "+" : ""}{Math.round(b.improvement_pct)}%
                          </span>
                        </div>
                        <div className="h-1 w-full bg-slate-950 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${b.improvement_pct > 0 ? "bg-emerald-500" : "bg-rose-500"} transition-all duration-500`}
                            style={{ width: `${Math.min(100, Math.abs(b.improvement_pct))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
