import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import * as api from "@/lib/api"
import { Palette, Type, Layout, Eye, Download, Wand2 } from "lucide-react"

export function DesignPage() {
  const [styles, setStyles] = useState<Array<Record<string, unknown>>>([])
  const [palettes, setPalettes] = useState<Array<Record<string, unknown>>>([])
  const [fonts, setFonts] = useState<Array<Record<string, unknown>>>([])
  const [suggestion, setSuggestion] = useState<Record<string, unknown> | null>(null)
  const [protoHtml, setProtoHtml] = useState("")
  const [protoTitle, setProtoTitle] = useState("My Prototype")
  const [protoStyle, setProtoStyle] = useState("glassmorphism")
  const [protoPalette, setProtoPalette] = useState("ocean")
  const [protoFont] = useState("modern")
  const [screenCount, setScreenCount] = useState(3)
  const [projectType, setProjectType] = useState("web")
  const [viewHtml, setViewHtml] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.listDesignStyles().then(setStyles).catch(() => {})
    api.listDesignPalettes().then(setPalettes).catch(() => {})
    api.listFontPairings().then(setFonts).catch(() => {})
  }, [])

  function hexColor(c: string) {
    return <div key={c} className="w-6 h-6 rounded-full border" style={{ backgroundColor: c }} title={c} />
  }

  async function handleSuggest() {
    setLoading(true)
    const s = await api.suggestDesign(projectType)
    setSuggestion(s)
    if ((s as any).style?.name) setProtoStyle((s as any).style.name.toLowerCase().replace(/\s+/g, "_"))
    if ((s as any).palette?.name) setProtoPalette((s as any).palette.name.toLowerCase().replace(/\s+/g, "_"))
    setLoading(false)
  }

  async function handleGeneratePrototype() {
    setLoading(true)
    const screens = Array.from({ length: screenCount }, (_, i) => ({
      name: `Screen ${i + 1}`,
      content: `<div class="card"><h3>Screen ${i + 1}</h3><p>Content for screen ${i + 1}</p></div>`,
    }))
    const result = await api.generatePrototype({
      title: protoTitle, screens,
      style: protoStyle, palette: protoPalette, font: protoFont,
    })
    setProtoHtml(result.html)
    setViewHtml(true)
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center gap-3 mb-8">
          <Palette className="h-7 w-7" />
          <div>
            <h1 className="text-3xl font-bold">Design Studio</h1>
            <p className="text-muted-foreground">Design intelligence + prototype generator — ui-ux-pro-max + huashu + taste-skill</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Wand2 className="h-4 w-4" />
                  Design Suggestion
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <Input placeholder="Project type (web, saas, ecommerce, portfolio...)" value={projectType} onChange={(e) => setProjectType(e.target.value)} />
                  <Button size="sm" onClick={handleSuggest} disabled={loading}><Wand2 className="mr-2 h-4 w-4" />Suggest</Button>
                </div>
                {suggestion && (
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div className="border rounded p-2">
                      <div className="text-xs font-medium text-muted-foreground">Style</div>
                      <div>{(suggestion as any).style?.name || "—"}</div>
                    </div>
                    <div className="border rounded p-2">
                      <div className="text-xs font-medium text-muted-foreground">Palette</div>
                      <div className="flex gap-1 mt-1">
                        {((suggestion as any).palette?.colors || []).map((c: string) => hexColor(c))}
                      </div>
                    </div>
                    <div className="border rounded p-2">
                      <div className="text-xs font-medium text-muted-foreground">Font</div>
                      <div>{(suggestion as any).font_pairing?.heading || "—"}</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Layout className="h-4 w-4" />
                  Prototype Generator
                </CardTitle>
                <CardDescription>huashu-style HTML prototype from config</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Title</Label>
                    <Input size={1} value={protoTitle} onChange={(e) => setProtoTitle(e.target.value)} />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Style</Label>
                    <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" value={protoStyle} onChange={(e) => setProtoStyle(e.target.value)}>
                      {styles.map((s: any) => <option key={s.name} value={s.name.toLowerCase().replace(/\s+/g, "_")}>{s.name}</option>)}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Palette</Label>
                    <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" value={protoPalette} onChange={(e) => setProtoPalette(e.target.value)}>
                      {palettes.map((p: any) => <option key={p.name} value={p.name.toLowerCase().replace(/\s+/g, "_")}>{p.name}</option>)}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Screens</Label>
                    <Input type="number" min={1} max={10} value={screenCount} onChange={(e) => setScreenCount(Number(e.target.value))} />
                  </div>
                </div>
                <Button onClick={handleGeneratePrototype} disabled={loading}>
                  {loading ? <Spinner className="mr-2 h-4 w-4" /> : <Eye className="mr-2 h-4 w-4" />}
                  Generate Prototype
                </Button>
              </CardContent>
            </Card>

            {viewHtml && protoHtml && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-sm">Preview</CardTitle>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => {
                      const blob = new Blob([protoHtml], { type: "text/html" })
                      const url = URL.createObjectURL(blob)
                      window.open(url, "_blank")
                    }}>
                      <Eye className="h-4 w-4 mr-1" /> Open
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => {
                      const blob = new Blob([protoHtml], { type: "text/html" })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement("a")
                      a.href = url; a.download = `${protoTitle.replace(/\s+/g, "-").toLowerCase()}.html`
                      a.click(); URL.revokeObjectURL(url)
                    }}>
                      <Download className="h-4 w-4 mr-1" /> Save
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <iframe
                    srcDoc={protoHtml}
                    className="w-full border rounded-lg"
                    style={{ height: "500px" }}
                    title="Prototype Preview"
                  />
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Layout className="h-4 w-4" />
                  Styles ({styles.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {styles.map((s: any) => (
                    <div key={s.name} className="text-xs border-b pb-2">
                      <div className="font-medium">{s.name}</div>
                      <div className="text-muted-foreground">{s.description?.slice(0, 80)}</div>
                      <div className="flex gap-1 mt-1">
                        {(s.tags || []).map((t: string) => <Badge key={t} variant="outline" className="text-[10px]">{t}</Badge>)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Palette className="h-4 w-4" />
                  Palettes ({palettes.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {palettes.map((p: any) => (
                    <div key={p.name} className="text-xs border-b pb-2">
                      <div className="font-medium">{p.name}</div>
                      <div className="flex gap-1 mt-1">{p.colors?.map((c: string) => hexColor(c))}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Type className="h-4 w-4" />
                  Fonts ({fonts.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 max-h-40 overflow-y-auto text-xs">
                  {fonts.map((f: any) => (
                    <div key={f.mood} className="flex justify-between border-b pb-1">
                      <span className="font-medium">{f.heading}</span>
                      <span className="text-muted-foreground">/{f.body}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
