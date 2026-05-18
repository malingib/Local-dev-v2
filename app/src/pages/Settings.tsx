import { useState, useEffect } from "react"
import { useAppStore } from "@/lib/store"
import { saveConfig } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"

export function Settings() {
  const { config, fetchConfig, health, fetchHealth } = useAppStore()
  const [googleKey, setGoogleKey] = useState("")
  const [groqKey, setGroqKey] = useState("")
  const [openrouterKey, setOpenrouterKey] = useState("")
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState("")
  const [results, setResults] = useState<Record<string, string>>({})

  useEffect(() => {
    fetchConfig()
    fetchHealth()
  }, [fetchConfig, fetchHealth])

  async function handleSaveKeys() {
    setSaving(true)
    setSaveMessage("")
    try {
      const body: Record<string, string> = {}
      if (googleKey) body.google_api_key = googleKey
      if (groqKey) body.groq_api_key = groqKey
      if (openrouterKey) body.openrouter_api_key = openrouterKey
      if (!googleKey && !groqKey && !openrouterKey) {
        setSaveMessage("Enter at least one key to save")
        setSaving(false)
        return
      }
      await saveConfig(body)
      setSaveMessage("Keys saved successfully (in-memory)")
      setGoogleKey("")
      setGroqKey("")
      setOpenrouterKey("")
      fetchHealth()
    } catch (e) {
      setSaveMessage(`Save failed: ${(e as Error).message}`)
    } finally {
      setSaving(false)
    }
  }

  async function handleTestKeys() {
    setTesting(true)
    setResults({})
    try {
      const res = await fetch("/api/config/validate-keys", { method: "POST" })
      const data = await res.json()
      setResults(data)
    } catch (e) {
      setResults({ error: (e as Error).message })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">Config Terminal</h1>
            <p className="text-slate-400 mt-1 font-mono text-sm uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-slate-500 animate-pulse" />
              Environment Variables & API Integration Matrix
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.history.back()}
            className="border border-slate-800 text-slate-500 hover:text-white uppercase text-[10px] font-bold tracking-widest px-4"
          >
            ← RETURN
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            {/* API Keys */}
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-4">
                <CardTitle className="text-white uppercase font-bold tracking-tight">Intelligence Bridges</CardTitle>
                <CardDescription className="text-slate-500 font-mono text-xs uppercase italic">Authentication required for LLM neural synthesis</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2 group">
                    <Label htmlFor="googleKey" className="text-[10px] font-bold text-slate-500 uppercase ml-1 flex items-center gap-2">
                      Google AI Studio Protocol
                      {health?.has_google_key && (
                        <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[8px] font-mono h-4">CONNECTED</Badge>
                      )}
                    </Label>
                    <Input
                      id="googleKey"
                      type="password"
                      placeholder="AIza_KEY_IDENTIFIER"
                      value={googleKey}
                      onChange={(e) => setGoogleKey(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs focus:ring-slate-500/50"
                    />
                    <p className="text-[10px] text-slate-600 font-mono italic">
                      Source: aistudio.google.com/app/apikey
                    </p>
                  </div>

                  <div className="space-y-2 group">
                    <Label htmlFor="groqKey" className="text-[10px] font-bold text-slate-500 uppercase ml-1 flex items-center gap-2">
                      Groq LP Core
                      {health?.has_groq_key && (
                        <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[8px] font-mono h-4">CONNECTED</Badge>
                      )}
                    </Label>
                    <Input
                      id="groqKey"
                      type="password"
                      placeholder="gsk_KEY_IDENTIFIER"
                      value={groqKey}
                      onChange={(e) => setGroqKey(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs focus:ring-slate-500/50"
                    />
                    <p className="text-[10px] text-slate-600 font-mono italic">
                      Source: console.groq.com/keys
                    </p>
                  </div>

                  <div className="space-y-2 group">
                    <Label htmlFor="openrouterKey" className="text-[10px] font-bold text-slate-500 uppercase ml-1 flex items-center gap-2">
                      OpenRouter Unified Gateway
                      {health?.has_openrouter_key && (
                        <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[8px] font-mono h-4">CONNECTED</Badge>
                      )}
                    </Label>
                    <Input
                      id="openrouterKey"
                      type="password"
                      placeholder="sk-or-KEY_IDENTIFIER"
                      value={openrouterKey}
                      onChange={(e) => setOpenrouterKey(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs focus:ring-slate-500/50"
                    />
                    <p className="text-[10px] text-slate-600 font-mono italic">
                      Source: openrouter.ai/keys
                    </p>
                  </div>
                </div>

                <div className="flex gap-3 pt-2">
                  <Button
                    onClick={handleSaveKeys}
                    disabled={saving}
                    className="flex-1 bg-slate-900 border border-slate-800 hover:border-slate-500/50 text-slate-200 font-black uppercase text-[10px] tracking-widest py-5"
                  >
                    {saving ? <Spinner className="mr-2" /> : null}
                    COMMIT KEYS
                  </Button>
                  <Button
                    onClick={handleTestKeys}
                    disabled={testing}
                    className="flex-1 bg-slate-100 hover:bg-white text-slate-950 font-black uppercase text-[10px] tracking-widest py-5"
                  >
                    {testing ? <Spinner className="mr-2" /> : null}
                    VAL_PROBE
                  </Button>
                </div>

                {saveMessage && (
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-800 text-[10px] font-mono text-slate-400 uppercase text-center italic tracking-widest">
                    SYSTEM: {saveMessage}
                  </div>
                )}

                {Object.keys(results).length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    {Object.entries(results).map(([provider, status]) => (
                      <div key={provider} className="flex items-center justify-between p-2 bg-slate-950 border border-slate-800 rounded">
                        <span className="text-[9px] font-bold text-slate-500 uppercase">{provider}</span>
                        <Badge variant={status === "ok" ? "default" : "destructive"} className="text-[8px] font-mono leading-none h-4">
                          {status.toUpperCase()}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3">
                <CardTitle className="text-white uppercase font-bold tracking-tight">System Environment</CardTitle>
                <CardDescription className="text-slate-500 font-mono text-[10px] uppercase">Persistent configurations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-slate-950/60 rounded-xl border border-slate-800 p-4">
                  <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                    Settings changes made in this terminal are <span className="text-amber-500 font-bold italic">TEMPORARY</span>.
                    To persist authentication tokens and project architecture settings across reboots,
                    edit the <code className="text-slate-200 bg-slate-900 px-1 py-0.5 rounded">.env</code>
                    matrix in the root directory directly.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            {/* Current Config */}
            {config && (
              <Card className="glass border-slate-800 bg-slate-900/40 sticky top-8">
                <CardHeader className="pb-4">
                  <CardTitle className="text-white uppercase font-bold tracking-tight">Active Blueprint</CardTitle>
                  <CardDescription className="text-slate-500 font-mono text-[10px] uppercase">Runtime state</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-1">
                    <div className="text-[9px] font-bold text-slate-600 uppercase">Current Project</div>
                    <div className="text-xs font-mono text-slate-200 bg-slate-950 border border-slate-800 p-2 rounded truncate">
                      {config.project_name || "NULL_WORKSPACE"}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-[9px] font-bold text-slate-600 uppercase">Operational Modules</div>
                    <div className="flex gap-1.5 flex-wrap">
                      {config.enabled_agents.map((agent) => (
                        <Badge key={agent} className="bg-slate-950 text-slate-400 border-slate-800 font-mono text-[9px] uppercase">
                          {agent}
                        </Badge>
                      ))}
                      {config.enabled_agents.length === 0 && (
                        <div className="text-[9px] text-slate-700 italic">NO_MODULES_LOADED</div>
                      )}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-800/50">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-slate-950/40 p-2 rounded border border-slate-800/50 text-center">
                        <div className="text-[8px] text-slate-600 uppercase font-bold">Uptime</div>
                        <div className="text-xs font-mono text-slate-400 mt-1">14:22:05</div>
                      </div>
                      <div className="bg-slate-950/40 p-2 rounded border border-slate-800/50 text-center">
                        <div className="text-[8px] text-slate-600 uppercase font-bold">Ver</div>
                        <div className="text-xs font-mono text-slate-400 mt-1">v2.4.0-REL</div>
                      </div>
                    </div>
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
