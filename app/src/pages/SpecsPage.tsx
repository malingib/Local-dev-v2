import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import * as api from "@/lib/api"
import { FileText, ListChecks, Code, Mic, Cpu } from "lucide-react"

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
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center gap-3 mb-8">
          <FileText className="h-7 w-7" />
          <div>
            <h1 className="text-3xl font-bold">Infrastructure</h1>
            <p className="text-muted-foreground">Spec-kit SDD + VibeVoice + TurboQuant + openvscode-server</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Spec-Driven Development
                </CardTitle>
                <CardDescription>github/spec-kit style Plan → Tasks → Implement</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <Label>Project Name</Label>
                  <Input value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="My Project" />
                </div>
                <div className="space-y-2">
                  <Label>Goal</Label>
                  <Textarea value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="What do you want to build?" className="min-h-[60px]" />
                </div>
                <div className="space-y-2">
                  <Label>Context (optional)</Label>
                  <Textarea value={context} onChange={(e) => setContext(e.target.value)} placeholder="Additional context..." className="min-h-[60px]" />
                </div>
                <Button onClick={handleCreateSpec} disabled={!goal || !projectName || loading}>
                  {loading ? <Spinner className="mr-2 h-4 w-4" /> : null}
                  Create Spec
                </Button>
              </CardContent>
            </Card>

            {specResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Latest Spec</CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2 max-h-60 overflow-y-auto">
                  <pre className="whitespace-pre-wrap font-mono">{JSON.stringify(specResult, null, 2)}</pre>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Mic className="h-4 w-4" />
                  Voice Interface
                </CardTitle>
                <CardDescription>VibeVoice-powered TTS for Buddy companion</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-xs text-muted-foreground">
                  Status: {(voiceStatus as any)?.detected_backend || "checking..."}
                  {(voiceStatus as any)?.has_vibevoice_key && <Badge className="ml-2 text-[10px]">VibeVoice key set</Badge>}
                  {(voiceStatus as any)?.has_elevenlabs_key && <Badge className="ml-2 text-[10px]">ElevenLabs key set</Badge>}
                </div>
                <div className="flex gap-2">
                  <Input value={speakText} onChange={(e) => setSpeakText(e.target.value)} placeholder="Text to speak..." />
                  <Button size="sm" onClick={handleSpeak} disabled={!speakText}>
                    <Mic className="h-4 w-4 mr-1" /> Speak
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Cpu className="h-4 w-4" />
                  LLM Optimizer
                </CardTitle>
                <CardDescription>TurboQuant KV cache compression config</CardDescription>
              </CardHeader>
              <CardContent>
                {optimizerConfig?.recommendations ? (
                  <div className="space-y-2 text-xs">
                    {(optimizerConfig.recommendations as Array<Record<string, unknown>> || []).map((r, i) => (
                      <div key={i} className="border rounded p-2">
                        <div className="font-medium">{r.strategy as string}</div>
                        <div className="text-muted-foreground">{r.reason as string}</div>
                        <Badge variant={r.priority === "high" ? "default" : "secondary"} className="text-[10px] mt-1">
                          {r.priority as string}
                        </Badge>
                      </div>
                    ))}
                    {(optimizerConfig.vllm_flags as string[] || []).length > 0 && (
                      <div className="mt-2">
                        <div className="font-medium text-muted-foreground mb-1">vLLM flags:</div>
                        <pre className="bg-muted p-2 rounded text-[10px]">{(optimizerConfig.vllm_flags as string[]).join("\n")}</pre>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">Auto-detecting GPU...</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  openvscode-server
                </CardTitle>
                <CardDescription>VS Code in your browser</CardDescription>
              </CardHeader>
              <CardContent>
                {vscodeStatus?.available ? (
                  <div className="text-xs space-y-2">
                    <Badge variant="default">Available</Badge>
                    <p className="text-muted-foreground">Run: <code className="bg-muted px-1 rounded">{((vscodeStatus as any).command as string)}</code></p>
                  </div>
                ) : (
                  <div className="text-xs space-y-2">
                    <Badge variant="secondary">Not installed</Badge>
                    <p className="text-muted-foreground">Install from GitHub:</p>
                    <pre className="bg-muted p-2 rounded text-[10px] whitespace-pre-wrap break-all">
                      {((vscodeStatus as any)?.install_command as string) || "See github.com/gitpod-io/openvscode-server"}
                    </pre>
                    <a href={((vscodeStatus as any)?.install_url as string) || "https://github.com/gitpod-io/openvscode-server"}
                       target="_blank" rel="noopener noreferrer"
                       className="text-primary underline">
                      GitHub Repository
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Saved Specs ({specs.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {specs.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No specs yet</p>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {specs.map((s: any) => (
                      <div key={s.id} className="flex items-center justify-between text-xs border-b pb-1">
                        <div className="truncate flex-1">
                          <span className="font-medium">{s.project}</span>
                          <span className="text-muted-foreground ml-1">— {s.goal}</span>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <Badge variant="outline" className="text-[10px]">{s.status}</Badge>
                          <Button size="sm" variant="ghost" className="h-5 w-5 p-0"
                                  onClick={() => handleGenerateTasks(s.id)}>
                            <ListChecks className="h-3 w-3" />
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
