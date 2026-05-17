import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import * as api from "@/lib/api"
import { Palette, Type, Layout, Eye, Download, Wand2, Box, Layers, Monitor } from "lucide-react"

export function DesignPage() {
  const [styles, setStyles] = useState<Array<Record<string, unknown>>>([])
  const [palettes, setPalettes] = useState<Array<Record<string, unknown>>>([])
  const [fonts, setFonts] = useState<Array<Record<string, unknown>>>([])
  const [suggestion, setSuggestion] = useState<Record<string, unknown> | null>(null)
  const [protoHtml, setProtoHtml] = useState("")
  const [protoTitle, setProtoTitle] = useState("SYSTEM_PROTOTYPE_ALPHA")
  const [protoStyle, setProtoStyle] = useState("glassmorphism")
  const [protoPalette, setProtoPalette] = useState("ocean")
  const [protoFont] = useState("modern")
  const [screenCount, setScreenCount] = useState(3)
  const [projectType, setProjectType] = useState("web_app")
  const [viewHtml, setViewHtml] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.listDesignStyles().then(setStyles).catch(() => {})
    api.listDesignPalettes().then(setPalettes).catch(() => {})
    api.listFontPairings().then(setFonts).catch(() => {})
  }, [])

  function hexColor(c: string) {
    return <div key={c} className="w-5 h-5 rounded border border-slate-800" style={{ backgroundColor: c }} title={c} />
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
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
              <Palette className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tighter text-white uppercase italic leading-none">Design Forge</h1>
              <p className="text-slate-500 mt-1 font-mono text-[10px] uppercase tracking-[0.3em]">Neural UI Synthesis & Visual Prototyping</p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-full">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Compiler Online</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-8 space-y-8">
            <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
              <div className="h-1 bg-gradient-to-r from-blue-600 to-indigo-600" />
              <CardHeader className="pb-4">
                <CardTitle className="text-white uppercase font-black text-lg tracking-tight flex items-center gap-2">
                  <Wand2 className="h-4 w-4 text-slate-400" />
                  Visual Synthesis Suggestion
                </CardTitle>
                <CardDescription className="font-mono text-[10px] uppercase text-slate-500">Heuristic styling based on project parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="flex-1">
                    <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1 mb-1.5 block">Project Architecture</Label>
                    <Input
                      placeholder="e.g., SAAS_DASHBOARD, CORE_ENGINE, WEB_INTERFACE..."
                      value={projectType}
                      onChange={(e) => setProjectType(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase tracking-widest h-11"
                    />
                  </div>
                  <Button
                    onClick={handleSuggest}
                    disabled={loading}
                    className="bg-slate-100 hover:bg-white text-slate-950 font-black uppercase text-[11px] tracking-widest h-11 px-8 sm:mt-6"
                  >
                    {loading ? <Spinner className="mr-2" /> : <Wand2 className="mr-2 h-4 w-4" />}
                    SYNTHESIZE
                  </Button>
                </div>

                {suggestion && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800/50">
                    <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 group hover:border-slate-500 transition-colors">
                      <div className="text-[9px] font-bold text-slate-600 uppercase mb-2">Styling Protocol</div>
                      <div className="text-xs font-mono text-white">{(suggestion as any).style?.name || "GENERIC_UI"}</div>
                    </div>
                    <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 group hover:border-slate-500 transition-colors">
                      <div className="text-[9px] font-bold text-slate-600 uppercase mb-2">Chromatic Matrix</div>
                      <div className="flex gap-1.5 mt-1">
                        {((suggestion as any).palette?.colors || []).map((c: string) => hexColor(c))}
                      </div>
                    </div>
                    <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 group hover:border-slate-500 transition-colors">
                      <div className="text-[9px] font-bold text-slate-600 uppercase mb-2">Typeface Weight</div>
                      <div className="text-xs font-mono text-white">{(suggestion as any).font_pairing?.heading || "SANS_MS"}</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-4">
                <CardTitle className="text-white uppercase font-black text-lg tracking-tight flex items-center gap-2">
                  <Box className="h-4 w-4 text-slate-400" />
                  Prototype Assembler
                </CardTitle>
                <CardDescription className="font-mono text-[10px] uppercase text-slate-500">Live HTML structural generation matrix</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Designation</Label>
                    <Input value={protoTitle} onChange={(e) => setProtoTitle(e.target.value)} className="bg-slate-950 border-slate-800 text-[10px] font-mono uppercase h-10" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Skin</Label>
                    <select className="flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-1 text-[10px] font-mono text-slate-300 uppercase outline-none focus:border-slate-500" value={protoStyle} onChange={(e) => setProtoStyle(e.target.value)}>
                      {styles.map((s: any) => <option key={s.name} value={s.name.toLowerCase().replace(/\s+/g, "_")}>{s.name.toUpperCase()}</option>)}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Palette</Label>
                    <select className="flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-1 text-[10px] font-mono text-slate-300 uppercase outline-none focus:border-slate-500" value={protoPalette} onChange={(e) => setProtoPalette(e.target.value)}>
                      {palettes.map((p: any) => <option key={p.name} value={p.name.toLowerCase().replace(/\s+/g, "_")}>{p.name.toUpperCase()}</option>)}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Screens</Label>
                    <Input type="number" min={1} max={10} value={screenCount} onChange={(e) => setScreenCount(Number(e.target.value))} className="bg-slate-950 border-slate-800 text-[10px] font-mono h-10" />
                  </div>
                </div>
                <Button
                  onClick={handleGeneratePrototype}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black uppercase text-[11px] tracking-widest h-12"
                >
                  {loading ? <Spinner className="mr-2" /> : <Layers className="mr-2 h-4 w-4" />}
                  GENERATE SOURCE ASSETS
                </Button>
              </CardContent>
            </Card>

            {viewHtml && protoHtml && (
              <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800 bg-slate-950/40 px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Monitor className="h-4 w-4 text-blue-500" />
                    <CardTitle className="text-xs font-mono uppercase tracking-widest text-slate-300">Live Virtualization</CardTitle>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="ghost" className="text-[10px] font-bold uppercase text-slate-500 hover:text-white" onClick={() => {
                      const blob = new Blob([protoHtml], { type: "text/html" })
                      const url = URL.createObjectURL(blob)
                      window.open(url, "_blank")
                    }}>
                      <Eye className="h-3 w-3 mr-1.5" /> DEPLOY_VIEW
                    </Button>
                    <Button size="sm" className="bg-slate-800 text-[10px] font-bold uppercase text-slate-200 hover:bg-slate-700" onClick={() => {
                      const blob = new Blob([protoHtml], { type: "text/html" })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement("a")
                      a.href = url; a.download = `${protoTitle.replace(/\s+/g, "-").toLowerCase()}.html`
                      a.click(); URL.revokeObjectURL(url)
                    }}>
                      <Download className="h-3 w-3 mr-1.5" /> EXPORT_HTML
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <iframe
                    srcDoc={protoHtml}
                    className="w-full bg-white"
                    style={{ height: "600px" }}
                    title="Prototype Preview"
                  />
                </CardContent>
              </Card>
            )}
          </div>

          <div className="lg:col-span-4 space-y-8">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3 border-b border-slate-800/50">
                <CardTitle className="text-[11px] font-black uppercase text-slate-500 tracking-[0.2em] flex items-center gap-2">
                  <Layers className="w-3 h-3" /> Visual Library
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-slate-800/50 max-h-[800px] overflow-y-auto custom-scrollbar">
                  <div className="p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Styles</h3>
                      <Badge className="bg-slate-800 text-[9px] font-mono">{styles.length}</Badge>
                    </div>
                    {styles.map((s: any) => (
                      <div key={s.name} className="group p-3 bg-slate-950/40 rounded-lg border border-transparent hover:border-slate-800 transition-all">
                        <div className="text-[10px] font-bold text-slate-200 uppercase">{s.name}</div>
                        <div className="text-[9px] text-slate-500 mt-1 line-clamp-2 italic">{s.description}</div>
                      </div>
                    ))}
                  </div>

                  <div className="p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Palettes</h3>
                      <Badge className="bg-slate-800 text-[9px] font-mono">{palettes.length}</Badge>
                    </div>
                    {palettes.map((p: any) => (
                      <div key={p.name} className="group p-3 bg-slate-950/40 rounded-lg border border-transparent hover:border-slate-800 transition-all">
                        <div className="text-[10px] font-bold text-slate-200 uppercase mb-2">{p.name}</div>
                        <div className="flex gap-1">{p.colors?.map((c: string) => hexColor(c))}</div>
                      </div>
                    ))}
                  </div>

                  <div className="p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Typography</h3>
                      <Badge className="bg-slate-800 text-[9px] font-mono">{fonts.length}</Badge>
                    </div>
                    <div className="grid grid-cols-1 gap-2">
                      {fonts.map((f: any) => (
                        <div key={f.mood} className="flex justify-between items-center p-2 bg-slate-950/60 rounded border border-slate-800/30">
                          <span className="text-[10px] font-bold text-slate-300 uppercase">{f.heading}</span>
                          <span className="text-[9px] font-mono text-slate-600">/ {f.body}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
