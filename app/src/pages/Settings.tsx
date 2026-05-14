import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { useAppStore } from "@/lib/store"
import { saveConfig } from "@/lib/api"

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
  }, [])

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
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center gap-3 mb-8">
          <Button variant="outline" size="sm" onClick={() => window.history.back()}>
            ← Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">Configure API keys and preferences</p>
          </div>
        </div>

        {/* API Keys */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
            <CardDescription>At least one API key is required for CodeAudit to work</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="googleKey">
                Google AI Studio Key{" "}
                {health?.has_google_key && (
                  <Badge variant="default" className="ml-2">Configured</Badge>
                )}
              </Label>
              <Input
                id="googleKey"
                type="password"
                placeholder="AIza..."
                value={googleKey}
                onChange={(e) => setGoogleKey(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Get your key at{" "}
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline"
                >
                  aistudio.google.com
                </a>
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="groqKey">
                Groq API Key{" "}
                {health?.has_groq_key && (
                  <Badge variant="default" className="ml-2">Configured</Badge>
                )}
              </Label>
              <Input
                id="groqKey"
                type="password"
                placeholder="gsk_..."
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Get your key at{" "}
                <a
                  href="https://console.groq.com/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline"
                >
                  console.groq.com
                </a>
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="openrouterKey">
                OpenRouter API Key{" "}
                {health?.has_openrouter_key && (
                  <Badge variant="default" className="ml-2">Configured</Badge>
                )}
              </Label>
              <Input
                id="openrouterKey"
                type="password"
                placeholder="sk-or-..."
                value={openrouterKey}
                onChange={(e) => setOpenrouterKey(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Get your key at{" "}
                <a
                  href="https://openrouter.ai/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline"
                >
                  openrouter.ai
                </a>
              </p>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleSaveKeys} disabled={saving}>
                {saving ? <Spinner className="mr-2" /> : null}
                Save Keys
              </Button>
              <Button onClick={handleTestKeys} disabled={testing}>
                {testing ? <Spinner className="mr-2" /> : null}
                Test Keys
              </Button>
            </div>
            {saveMessage && (
              <p className="text-sm text-muted-foreground">{saveMessage}</p>
            )}
            {Object.keys(results).length > 0 && (
              <div className="space-y-1 text-sm">
                {Object.entries(results).map(([provider, status]) => (
                  <div key={provider} className="flex items-center gap-2">
                    <Badge variant={status === "ok" ? "default" : "destructive"}>
                      {provider}
                    </Badge>
                    <span className="text-muted-foreground">{status}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Current Config */}
        {config && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Current Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="font-medium">Project</dt>
                  <dd>{config.project_name}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="font-medium">Enabled Agents</dt>
                  <dd className="flex gap-1 flex-wrap justify-end">
                    {config.enabled_agents.map((agent) => (
                      <Badge key={agent} variant="outline" className="text-xs">
                        {agent}
                      </Badge>
                    ))}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        )}

        {/* Note */}
        <Card>
          <CardHeader>
            <CardTitle>Environment Variables</CardTitle>
            <CardDescription>
              For permanent configuration, edit the <code className="text-xs">.env</code> file in the codeaudit directory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Settings changes made here are temporary. To persist API keys and project settings,
              edit the <code>.env</code> file in the backend directory directly.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
