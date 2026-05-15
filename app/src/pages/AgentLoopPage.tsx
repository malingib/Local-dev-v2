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
  XCircle, Brain, Zap, Target,
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
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center gap-3 mb-8">
          <Brain className="h-7 w-7" />
          <div>
            <h1 className="text-3xl font-bold">Agent Loop</h1>
            <p className="text-muted-foreground">HALO-style self-improving agent loop — trace, analyze, improve, repeat</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Configuration</CardTitle>
                <CardDescription>Set up the self-improvement loop</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="aloopSession">Session ID</Label>
                    <Input id="aloopSession" placeholder="session-id or leave empty" value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="aloopTarget">Target File (for auto-fix)</Label>
                    <Input id="aloopTarget" placeholder="path/to/file.py" value={targetFile} onChange={(e) => setTargetFile(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="aloopIters">Iterations</Label>
                    <Input id="aloopIters" type="number" value={iterations} onChange={(e) => setIterations(Number(e.target.value))} />
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <Button onClick={handleAnalyze} disabled={loading}>
                    {loading ? <Spinner className="mr-2 h-4 w-4" /> : <Activity className="mr-2 h-4 w-4" />}
                    Analyze Traces
                  </Button>
                  <Button variant="secondary" onClick={handleGenerateImprovements} disabled={loading}>
                    <Lightbulb className="mr-2 h-4 w-4" />
                    Generate Improvements
                  </Button>
                  <Button variant="default" onClick={handleRunLoop} disabled={loopLoading} className="bg-primary">
                    {loopLoading ? <Spinner className="mr-2 h-4 w-4" /> : <RotateCcw className="mr-2 h-4 w-4" />}
                    Run Full Loop
                  </Button>
                </div>
              </CardContent>
            </Card>

            {analysis && !(analysis as any).error && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    Trace Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div className="border rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold">{(analysis as any).total}</div>
                      <div className="text-xs text-muted-foreground">Total Traces</div>
                    </div>
                    <div className="border rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-green-500">{(analysis as any).success_rate}%</div>
                      <div className="text-xs text-muted-foreground">Success Rate</div>
                    </div>
                    <div className="border rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold">{(analysis as any).failures}</div>
                      <div className="text-xs text-muted-foreground">Failures</div>
                    </div>
                    <div className="border rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold">{Math.round((analysis as any).avg_duration_ms)}ms</div>
                      <div className="text-xs text-muted-foreground">Avg Duration</div>
                    </div>
                  </div>
                  {analysis && (analysis as any).agents && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {Object.entries((analysis as any).agents as Record<string, number>).map(([agent, count]) => (
                        <Badge key={agent} variant="outline">{agent}: {String(count)}</Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {improvements.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Lightbulb className="h-4 w-4" />
                    Improvements ({improvements.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {improvements.map((imp: any, i) => (
                    <div key={i} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <Badge variant={imp.impact_score > 7 ? "default" : "secondary"} className="text-[10px]">
                            {imp.category}
                          </Badge>
                          <span className="font-medium text-sm">{imp.description}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">score: {imp.impact_score}/10</span>
                          {imp.applied ? <CheckCircle2 className="h-4 w-4 text-green-500" /> : null}
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground mb-2">{imp.suggestion}</p>
                      {!imp.applied && (
                        <Button size="sm" variant="outline" onClick={() => handleApply(imp.id)} disabled={loading}>
                          Apply
                        </Button>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {loopResults && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    Loop Results
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {loopResults.map((r: any, i) => (
                    <div key={i} className="border rounded-lg p-3">
                      <div className="font-medium text-sm mb-1">Iteration {r.iteration}</div>
                      <div className="text-xs text-muted-foreground">
                        Improvements found: {r.improvements_found}
                      </div>
                      {r.applied && r.applied.map((a: any, j: number) => (
                        <div key={j} className="text-xs flex items-center gap-1 mt-1">
                          {a.status === "applied" ? (
                            <CheckCircle2 className="h-3 w-3 text-green-500" />
                          ) : (
                            <XCircle className="h-3 w-3 text-muted-foreground" />
                          )}
                          {a.status}: {a.suggestion?.slice(0, 60)}...
                        </div>
                      ))}
                      {r.benchmark && r.benchmark.metrics && (
                        <div className="text-xs text-muted-foreground mt-2">
                          Baseline: {Math.round(r.benchmark.metrics.avg_duration_ms)}ms avg,{" "}
                          {Math.round(r.benchmark.metrics.success_rate)}% success
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Recent Traces</CardTitle>
              </CardHeader>
              <CardContent>
                {traces.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No traces yet</p>
                ) : (
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {traces.slice(0, 20).map((t: any) => (
                      <div key={t.id} className="flex items-center gap-2 text-xs border-b pb-1">
                        {t.success ? (
                          <CheckCircle2 className="h-3 w-3 text-green-500 shrink-0" />
                        ) : (
                          <XCircle className="h-3 w-3 text-red-500 shrink-0" />
                        )}
                        <span className="truncate flex-1">{t.action || t.tool || "—"}</span>
                        <span className="text-muted-foreground shrink-0">{t.duration_ms}ms</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {benchmarks.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    Benchmarks
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-xs">
                    {benchmarks.slice(0, 10).map((b: any) => (
                      <div key={b.id} className="flex justify-between border-b pb-1">
                        <span className="text-muted-foreground">{b.metric_name}</span>
                        <span className={b.improvement_pct > 0 ? "text-green-500" : "text-red-500"}>
                          {b.improvement_pct > 0 ? "+" : ""}{Math.round(b.improvement_pct)}%
                        </span>
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
