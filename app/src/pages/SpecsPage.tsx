import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import * as api from "@/lib/api"
import { FileText, ListChecks, Code, Mic, Cpu, Terminal, Zap, Globe } from "lucide-react"

export function SpecsPage() {
  const [specs, setSpecs] = useState<Array<Record<string, unknown>>>([])
  const [goal, setGoal] = useState("")
  const [projectName, setProjectName] = useState("")
  const [context, setContext] = useState("")
  const [specResult, setSpecResult] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState<Record<string, unknown> | null>(null)
  const [speakText, setSpeakText] = useState("")
  const [optimizerConfig, setOptimizerConfig] = useState<Record<string, unknown> | null>(null)
  const [vscodeStatus, setVscodeStatus] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    api.listSpecs().then(setSpecs).catch(() => {})
    api.getVoiceStatus().then(setVoiceStatus).catch(() => {})
    api.getVscodeStatus().then(setVscodeStatus).catch(() => {})
    api.getOptimizerConfig().then(setOptimizerConfig).catch(() => {})
  }, [])

  async function handleCreateSpec() {
    if (!goal || !projectName) return
    setLoading(true)
    const result = await api.createSpec({ project_name: projectName, goal, context })
    setSpecResult(result)
    await api.listSpecs().then(setSpecs)
    setLoading(false)
  }

  async function handleGenerateTasks(specId: string) {
    setLoading(true)
    await api.generateSpecTasks(specId)
    await api.listSpecs().then(setSpecs)
    setLoading(false)
  }

  async function handleSpeak() {
    if (!speakText) return
    await api.speakVoice(speakText)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
              <FileText className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tighter text-white uppercase italic leading-none">Infrastructure</h1>
              <p className="text-slate-500 mt-1 font-mono text-[10px] uppercase tracking-[0.3em]">Spec-Kit SDD & VibeVoice Integration Terminal</p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-3">
            <div className="px-4 py-2 bg-slate-900/50 border border-slate-800 rounded flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Voice Core: ONLINE</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7 space-y-8">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-4 border-b border-slate-800/50 mb-6">
                <CardTitle className="text-white uppercase font-black text-lg tracking-tight flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-slate-400" />
                  Spec-Driven Development Matrix
                </CardTitle>
                <CardDescription className="font-mono text-[10px] uppercase text-slate-500 italic">Plan → Tasks → Autonomous Implementation Loop</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Project Designation</Label>
                    <Input
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                      placeholder="e.g. NEURAL_SYNAPSE_v2"
                      className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase tracking-widest h-11"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Mission Goal</Label>
                    <Textarea
                      value={goal}
                      onChange={(e) => setGoal(e.target.value)}
                      placeholder="Define the primary objective of this build sequence..."
                      className="bg-slate-950 border-slate-800 text-[11px] font-mono min-h-[100px] uppercase"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Contextual Parameters</Label>
                    <Textarea
                      value={context}
                      onChange={(e) => setContext(e.target.value)}
                      placeholder="Additional environment data or constraints..."
                      className="bg-slate-950 border-slate-800 text-[11px] font-mono min-h-[80px] uppercase"
                    />
                  </div>
                </div>
                <Button
                  onClick={handleCreateSpec}
                  disabled={!goal || !projectName || loading}
                  className="w-full bg-slate-100 hover:bg-white text-slate-950 font-black uppercase text-[12px] tracking-[0.2em] h-12"
                >
                  {loading ? <Spinner className="mr-2" /> : <Zap className="mr-2 h-4 w-4" />}
                  INITIALIZE SPEC
                </Button>
              </CardContent>
            </Card>

            {specResult && (
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-2">
                  <CardTitle className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Active Blueprint Source</CardTitle>
                </CardHeader>
                <CardContent className="pt-2">
                  <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 max-h-[300px] overflow-y-auto custom-scrollbar">
                    <pre className="text-[10px] font-mono text-emerald-500 leading-relaxed">{JSON.stringify(specResult, null, 2)}</pre>
                  </div>
                </CardContent>
              </Card>
            )}

            <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
              <div className="h-1 bg-gradient-to-r from-rose-600 to-amber-600" />
              <CardHeader className="pb-4">
                <CardTitle className="text-white uppercase font-black text-lg tracking-tight flex items-center gap-2">
                  <Mic className="h-4 w-4 text-slate-400" />
                  VibeVoice Interface
                </CardTitle>
                <CardDescription className="font-mono text-[10px] uppercase text-slate-500">Audio synthesis for companion interaction</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-slate-950 border border-slate-800 rounded-lg">
                  <Globe className="h-3 w-3 text-slate-600" />
                  <span className="text-[9px] font-mono text-slate-400 uppercase tracking-widest">
                    Detected Backend: <span className="text-white">{(voiceStatus as any)?.detected_backend || "SCANNING..."}</span>
                  </span>
                  <div className="flex gap-2 ml-auto">
                    {(voiceStatus as any)?.has_vibevoice_key && <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[8px] font-mono">VIBE_KEY</Badge>}
                    {(voiceStatus as any)?.has_elevenlabs_key && <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/20 text-[8px] font-mono">11LABS_KEY</Badge>}
                  </div>
                </div>
                <div className="flex gap-3">
                  <Input
                    value={speakText}
                    onChange={(e) => setSpeakText(e.target.value)}
                    placeholder="ENTER PHRASE FOR SYNTHESIS..."
                    className="bg-slate-950 border-slate-800 text-[10px] font-mono h-11"
                  />
                  <Button
                    onClick={handleSpeak}
                    disabled={!speakText}
                    className="bg-slate-900 border border-slate-800 text-slate-200 font-bold uppercase text-[10px] tracking-widest px-6"
                  >
                    SYNTHESIZE
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-5 space-y-8">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3 border-b border-slate-800/50">
                <CardTitle className="text-[11px] font-black uppercase text-slate-500 tracking-[0.2em] flex items-center gap-2">
                  <Cpu className="w-3 h-3" /> Hardware Optimizer
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {optimizerConfig?.recommendations ? (
                  <div className="space-y-4">
                    {(optimizerConfig.recommendations as Array<Record<string, unknown>> || []).map((r, i) => (
                      <div key={i} className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 group hover:border-slate-500 transition-all">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-[10px] font-black text-white uppercase tracking-tight">{r.strategy as string}</div>
                          <Badge className={`${r.priority === "high" ? "bg-rose-500/10 text-rose-500 border-rose-500/20" : "bg-slate-800 text-slate-400"} text-[8px] font-mono h-4`}>
                            {r.priority as string}
                          </Badge>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono leading-relaxed italic">{r.reason as string}</div>
                      </div>
                    ))}
                    {(optimizerConfig.vllm_flags as string[] || []).length > 0 && (
                      <div className="mt-4">
                        <div className="text-[9px] font-bold text-slate-600 uppercase mb-2">vLLM Optimization Flags</div>
                        <div className="bg-black/40 border border-slate-800 p-3 rounded font-mono text-[9px] text-emerald-500 leading-tight">
                          {(optimizerConfig.vllm_flags as string[]).join("\n")}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8">
                    <Spinner className="w-6 h-6 border-slate-800 border-t-slate-500 mb-4" />
                    <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">Scanning Hardware...</span>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3 border-b border-slate-800/50">
                <CardTitle className="text-[11px] font-black uppercase text-slate-500 tracking-[0.2em] flex items-center gap-2">
                  <Code className="w-3 h-3" /> IDE Virtualization
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {vscodeStatus?.available ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[9px] font-mono">READY</Badge>
                      <span className="text-[10px] font-mono text-slate-400 uppercase">VSCODE_SERVER_LOADED</span>
                    </div>
                    <div className="bg-slate-950 p-4 border border-slate-800 rounded-lg">
                      <div className="text-[8px] font-bold text-slate-600 uppercase mb-2">Execute Command</div>
                      <code className="text-[10px] font-mono text-blue-400">
                        {((vscodeStatus as any).command as string)}
                      </code>
                    </div>
                    <Button className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold uppercase text-[10px] tracking-widest h-10">
                      LAUNCH_BROWSER_IDE
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="text-slate-500 border-slate-800 text-[9px] font-mono">NOT_DETECTED</Badge>
                      <span className="text-[10px] font-mono text-slate-600 uppercase">OpenVSCode Missing</span>
                    </div>
                    <div className="bg-slate-950 p-4 border border-slate-800 rounded-lg">
                      <div className="text-[8px] font-bold text-slate-600 uppercase mb-2">Install Protocol</div>
                      <pre className="text-[9px] font-mono text-slate-500 whitespace-pre-wrap break-all leading-tight">
                        {((vscodeStatus as any)?.install_command as string) || "See github.com/gitpod-io/openvscode-server"}
                      </pre>
                    </div>
                    <Button variant="outline" className="w-full border-slate-800 text-slate-500 text-[10px] font-bold uppercase tracking-widest h-10">
                      SOURCE_FROM_GITHUB
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3 border-b border-slate-800/50">
                <CardTitle className="text-[11px] font-black uppercase text-slate-500 tracking-[0.2em] flex items-center justify-between">
                  Mission Specs <span className="text-slate-600 font-mono text-[9px]">{specs.length}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {specs.length === 0 ? (
                  <div className="py-12 text-center">
                    <span className="text-[10px] font-mono text-slate-700 uppercase italic">NO_RECORDS_FOUND</span>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-800/50 max-h-[300px] overflow-y-auto custom-scrollbar">
                    {specs.map((s: any) => (
                      <div key={s.id} className="p-4 flex items-center justify-between group hover:bg-slate-800/30 transition-all">
                        <div className="truncate flex-1">
                          <div className="text-[10px] font-bold text-white uppercase truncate">{s.project}</div>
                          <div className="text-[9px] text-slate-500 font-mono mt-0.5 truncate italic">{s.goal}</div>
                        </div>
                        <div className="flex items-center gap-3 ml-4">
                          <Badge variant="outline" className="text-[8px] font-mono text-slate-400 border-slate-800 uppercase">{s.status}</Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 w-7 p-0 text-slate-500 hover:text-white"
                            onClick={() => handleGenerateTasks(s.id)}
                          >
                            <ListChecks className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
