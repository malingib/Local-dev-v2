import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import * as api from "@/lib/api"
import {
  Share2, FileSearch, GitBranch, BarChart3,
  Download, Scan,
} from "lucide-react"

export function GraphPage() {
  const [projectPath, setProjectPath] = useState("")
  const [graphs, setGraphs] = useState<Array<Record<string, unknown>>>([])
  const [currentGraph, setCurrentGraph] = useState<Record<string, unknown> | null>(null)
  const [architecture, setArchitecture] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState("")
  const [searchResults, setSearchResults] = useState<Array<Record<string, unknown>>>([])
  const [fileDeps, setFileDeps] = useState<Record<string, unknown> | null>(null)
  const [depTarget, setDepTarget] = useState("")
  const [extractPath, setExtractPath] = useState("")
  const [extractResult, setExtractResult] = useState<Record<string, unknown> | null>(null)
  const [extractLoading, setExtractLoading] = useState(false)

  useEffect(() => {
    api.listKnowledgeGraphs().then(setGraphs).catch(() => {})
  }, [])

  async function handleScan() {
    if (!projectPath) return
    setLoading(true)
    try {
      const result = await api.scanProjectGraph(projectPath)
      setCurrentGraph(result)
      const loaded = await api.loadProjectGraph(projectPath)
      setArchitecture(loaded.architecture)
      await api.listKnowledgeGraphs().then(setGraphs)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  async function handleSearch() {
    if (!projectPath || !search) return
    const results = await api.queryKnowledgeGraph(projectPath, undefined, search)
    setSearchResults([...results.nodes, ...results.edges])
  }

  async function handleDeps() {
    if (!projectPath || !depTarget) return
    const deps = await api.getFileDependencies(projectPath, depTarget)
    setFileDeps(deps)
  }

  async function handleExtract() {
    if (!extractPath) return
    setExtractLoading(true)
    try {
      const result = await api.extractAllLayers(extractPath)
      setExtractResult(result)
    } catch (e) {
      console.error(e)
    }
    setExtractLoading(false)
  }

  const nodeCount = (currentGraph as any)?.nodes?.length ?? 0
  const edgeCount = (currentGraph as any)?.edges?.length ?? 0

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">Project Map</h1>
            <p className="text-slate-400 mt-1 font-mono text-sm uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
              Neural Codebase Topology & Dependency Matrix
            </p>
          </div>
          <div className="px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg backdrop-blur-sm">
            <div className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Analysis Depth</div>
            <div className="text-xl font-mono text-indigo-400 font-bold">L5 DISTILL</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader>
                <CardTitle className="text-white uppercase tracking-tight font-bold flex items-center gap-2">
                  <Scan className="h-5 w-5 text-indigo-400" />
                  Topographic Analysis
                </CardTitle>
                <CardDescription className="text-slate-500 font-mono text-xs uppercase italic">Synchronize local repository with knowledge graph</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="/absolute/path/to/project"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    className="flex-1 bg-slate-950 border-slate-800 text-indigo-100 font-mono text-sm focus:ring-indigo-500/50"
                  />
                  <Button
                    onClick={handleScan}
                    disabled={!projectPath || loading}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold uppercase tracking-widest text-xs px-6"
                  >
                    {loading ? <Spinner className="mr-2 h-4 w-4" /> : <Share2 className="mr-2 h-4 w-4" />}
                    INITIALIZE
                  </Button>
                </div>
                {currentGraph && (
                  <div className="grid grid-cols-3 gap-4 pt-2">
                    <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-center">
                      <div className="text-2xl font-mono font-black text-indigo-400">{nodeCount}</div>
                      <div className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Nodes</div>
                    </div>
                    <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-center">
                      <div className="text-2xl font-mono font-black text-indigo-400">{edgeCount}</div>
                      <div className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Edges</div>
                    </div>
                    <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-center">
                      <div className="text-2xl font-mono font-black text-indigo-400">
                        {edgeCount > 0 ? (nodeCount / edgeCount).toFixed(2) : "0.0"}
                      </div>
                      <div className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Density</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-bold text-slate-200 uppercase tracking-widest flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-indigo-400" />
                    Architecture
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {architecture ? (
                    <div className="space-y-4">
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(architecture.layers as Record<string, number> || {}).map(([layer, count]) => (
                          <Badge key={layer} className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 font-mono text-[10px]">
                            {layer.toUpperCase()}: {String(count)}
                          </Badge>
                        ))}
                      </div>
                      <div className="space-y-2">
                        <div className="text-[10px] font-bold text-slate-500 uppercase">Node Distribution</div>
                        <div className="flex flex-wrap gap-1.5">
                          {Object.entries(architecture.node_types as Record<string, number> || {}).map(([t, c]) => (
                            <Badge key={t} variant="outline" className="text-[9px] border-slate-800 text-slate-400 bg-slate-950 px-1.5 py-0.5">
                              {t}: {String(c)}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-6 border border-dashed border-slate-800 rounded-lg">
                      <p className="text-[10px] text-slate-600 font-mono uppercase">Waiting for scan data...</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-bold text-slate-200 uppercase tracking-widest flex items-center gap-2">
                    <FileSearch className="h-4 w-4 text-indigo-400" />
                    Neural Search
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Node identifier..."
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="h-8 bg-slate-950 border-slate-800 text-xs font-mono"
                    />
                    <Button size="sm" onClick={handleSearch} disabled={!search || !projectPath} className="h-8 bg-slate-800 hover:bg-slate-700 uppercase text-[10px] font-bold">
                      QUERY
                    </Button>
                  </div>
                  {searchResults.length > 0 && (
                    <div className="max-h-32 overflow-y-auto space-y-1 scrollbar-hide">
                      {searchResults.slice(0, 30).map((r, i) => (
                        <div key={i} className="flex items-center gap-2 p-1.5 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                          <Badge className="bg-slate-800 text-slate-400 border-none text-[8px] font-mono leading-none h-4 px-1">{String((r as any).type).toUpperCase()}</Badge>
                          <span className="font-mono text-[10px] text-slate-300 truncate">{(r as any).label}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-slate-200 uppercase tracking-widest flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-indigo-400" />
                  Dependency Slicing
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Relative path (e.g. src/app.tsx)"
                    value={depTarget}
                    onChange={(e) => setDepTarget(e.target.value)}
                    className="flex-1 bg-slate-950 border-slate-800 text-xs font-mono"
                  />
                  <Button size="sm" onClick={handleDeps} disabled={!depTarget || !projectPath} className="bg-slate-800 hover:bg-slate-700 uppercase text-[10px] font-bold">
                    SLICE
                  </Button>
                </div>
                {fileDeps && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-2">
                        <div className="w-1 h-1 rounded-full bg-blue-500" /> Inbound (Imports)
                      </div>
                      <div className="bg-slate-950/40 rounded border border-slate-800 p-2 min-h-20 max-h-40 overflow-y-auto">
                        {(fileDeps.imports as Array<Record<string, unknown>> || []).slice(0, 10).map((imp, i) => (
                          <div key={i} className="text-[10px] font-mono text-slate-400 border-b border-slate-900 pb-1 mb-1 last:border-0">{(imp as any).name}</div>
                        ))}
                        {(fileDeps.imports as Array<Record<string, unknown>> || []).length === 0 && (
                          <div className="text-[10px] text-slate-700 italic">No inbound links found</div>
                        )}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-2">
                        <div className="w-1 h-1 rounded-full bg-purple-500" /> Outbound (Dependents)
                      </div>
                      <div className="bg-slate-950/40 rounded border border-slate-800 p-2 min-h-20 max-h-40 overflow-y-auto">
                        {(fileDeps.dependents as string[] || []).slice(0, 10).map((dep, i) => (
                          <div key={i} className="text-[10px] font-mono text-slate-400 border-b border-slate-900 pb-1 mb-1 last:border-0">{dep}</div>
                        ))}
                        {(fileDeps.dependents as string[] || []).length === 0 && (
                          <div className="text-[10px] text-slate-700 italic">No outbound links found</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
              <div className="h-1 w-full bg-indigo-600/50" />
              <CardHeader>
                <CardTitle className="text-white uppercase tracking-tight font-bold flex items-center gap-2">
                  <Download className="h-5 w-5 text-indigo-400" />
                  Neural Distill
                </CardTitle>
                <CardDescription className="text-slate-500 font-mono text-xs uppercase italic">Compress codebase into L1-L5 semantic layers</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Absolute path to target file"
                    value={extractPath}
                    onChange={(e) => setExtractPath(e.target.value)}
                    className="flex-1 bg-slate-950 border-slate-800 text-indigo-100 font-mono text-sm"
                  />
                  <Button
                    size="sm"
                    onClick={handleExtract}
                    disabled={!extractPath || extractLoading}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold uppercase tracking-widest text-xs"
                  >
                    {extractLoading ? <Spinner className="mr-2 h-4 w-4" /> : "EXTRACT"}
                  </Button>
                </div>
                {extractResult && !(extractResult as any).error && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-5 gap-2">
                      {['L1', 'L2', 'L3', 'L4', 'L5'].map((l) => (
                        <div key={l} className="bg-slate-950 border border-slate-800 rounded-lg p-2 text-center group hover:border-indigo-500 transition-colors">
                          <div className="text-sm font-black text-indigo-400">{l}</div>
                          <div className="text-[8px] text-slate-600 uppercase font-bold group-hover:text-slate-400">Layer</div>
                        </div>
                      ))}
                    </div>
                    {extractResult && (extractResult as any).summary && (
                      <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800/50 flex justify-between items-center text-[10px] font-mono">
                        <div className="flex gap-4">
                          <div className="text-slate-500">RAW: <span className="text-slate-200">{(extractResult as any).summary.raw_tokens}</span></div>
                          <div className="text-slate-500">DISTILLED: <span className="text-indigo-400">{(extractResult as any).summary.total_extracted_tokens}</span></div>
                        </div>
                        <div className="text-indigo-500 font-bold italic">
                          COMPRESSION: {(extractResult as any).summary.compression_ratio}%
                        </div>
                      </div>
                    )}
                  </div>
                )}
                {(extractResult as any)?.error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded p-3 text-red-400 text-xs font-mono">
                    ERROR: {(extractResult as any).error}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="glass border-slate-800 bg-slate-900/40 sticky top-8">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-slate-200 uppercase tracking-widest">Library</CardTitle>
                <CardDescription className="text-slate-500 font-mono text-[10px] uppercase">Stored Topologies</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {graphs.length === 0 ? (
                  <div className="text-center py-8 bg-slate-950/40 rounded border border-dashed border-slate-800">
                    <p className="text-[10px] text-slate-600 uppercase italic">Empty Archive</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {graphs.map((g: any, i) => (
                      <div
                        key={i}
                        className="group relative bg-slate-950/60 border border-slate-800 rounded-xl p-3 cursor-pointer hover:border-indigo-500/50 transition-all duration-300"
                        onClick={async () => {
                          setProjectPath(g.name)
                          const loaded = await api.loadProjectGraph(g.name)
                          setCurrentGraph(loaded.graph)
                          setArchitecture(loaded.architecture)
                        }}
                      >
                        <div className="font-bold text-slate-300 group-hover:text-white transition-colors text-xs truncate max-w-[180px] mb-1">{g.name}</div>
                        <div className="flex items-center gap-2 text-[9px] font-mono text-slate-500 mb-2">
                          <span className="text-indigo-400 font-bold">{g.nodes} NODES</span>
                          <span className="w-1 h-1 rounded-full bg-slate-800" />
                          <span>{g.edges} EDGES</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(g.layers || {}).map(([layer, count]) => (
                            <span key={layer} className="text-[8px] font-bold text-slate-600 bg-slate-900 px-1 rounded border border-slate-800 uppercase">
                              {layer}: {String(count)}
                            </span>
                          ))}
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
