import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import * as api from "@/lib/api"
import {
  Share2, FileSearch, GitBranch, BarChart3, Layers,
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
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center gap-3 mb-8">
          <Share2 className="h-7 w-7" />
          <div>
            <h1 className="text-3xl font-bold">Knowledge Graph</h1>
            <p className="text-muted-foreground">Multi-agent codebase analysis — Understand-Anything + graphify + distil</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Scan Project</CardTitle>
                <CardDescription>Build a knowledge graph of all files, functions, classes, and dependencies</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="/path/to/project"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    className="flex-1"
                  />
                  <Button onClick={handleScan} disabled={!projectPath || loading}>
                    {loading ? <Spinner className="mr-2 h-4 w-4" /> : <Scan className="mr-2 h-4 w-4" />}
                    Scan
                  </Button>
                </div>
                {currentGraph && (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="border rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-primary">{nodeCount}</div>
                      <div className="text-xs text-muted-foreground">Nodes</div>
                    </div>
                    <div className="border rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-primary">{edgeCount}</div>
                      <div className="text-xs text-muted-foreground">Edges</div>
                    </div>
                    <div className="border rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-primary">
                        {edgeCount > 0 ? (nodeCount / edgeCount).toFixed(2) : "—"}
                      </div>
                      <div className="text-xs text-muted-foreground">Density</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Architecture
                </CardTitle>
              </CardHeader>
              <CardContent>
                {architecture ? (
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(architecture.layers as Record<string, number> || {}).map(([layer, count]) => (
                        <Badge key={layer} variant="outline" className="text-xs">
                          <Layers className="h-3 w-3 mr-1" />
                          {layer}: {String(count)}
                        </Badge>
                      ))}
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">Node types:</div>
                      <div>
                        {Object.entries(architecture.node_types as Record<string, number> || {}).map(([t, c]) => (
                          <Badge key={t} variant="secondary" className="text-[10px] mr-1 mb-1">{t}: {String(c)}</Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Scan a project to see architecture analysis</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <FileSearch className="h-4 w-4" />
                  Graph Search
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <Input
                    placeholder="Search nodes by name or path..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="flex-1"
                  />
                  <Button size="sm" onClick={handleSearch} disabled={!search || !projectPath}>
                    Search
                  </Button>
                </div>
                {searchResults.length > 0 && (
                  <div className="max-h-40 overflow-y-auto space-y-1 text-sm">
                    {searchResults.slice(0, 30).map((r, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs border-b pb-1">
                        <Badge variant="outline" className="text-[10px]">{String((r as any).type)}</Badge>
                        <span className="font-mono">{(r as any).label}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <GitBranch className="h-4 w-4" />
                  File Dependencies
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <Input
                    placeholder="Relative file path (e.g., src/main.py)"
                    value={depTarget}
                    onChange={(e) => setDepTarget(e.target.value)}
                    className="flex-1"
                  />
                  <Button size="sm" onClick={handleDeps} disabled={!depTarget || !projectPath}>
                    Analyze
                  </Button>
                </div>
                {fileDeps && (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="font-medium text-xs text-muted-foreground mb-1">Imports</div>
                      {(fileDeps.imports as Array<Record<string, unknown>> || []).slice(0, 10).map((imp, i) => (
                        <div key={i} className="text-xs font-mono">{(imp as any).name}</div>
                      ))}
                      {(fileDeps.imports as Array<Record<string, unknown>> || []).length === 0 && (
                        <div className="text-xs text-muted-foreground">None found</div>
                      )}
                    </div>
                    <div>
                      <div className="font-medium text-xs text-muted-foreground mb-1">Dependents</div>
                      {(fileDeps.dependents as string[] || []).slice(0, 10).map((dep, i) => (
                        <div key={i} className="text-xs font-mono">{dep}</div>
                      ))}
                      {(fileDeps.dependents as string[] || []).length === 0 && (
                        <div className="text-xs text-muted-foreground">None</div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  Distil: Code Extraction (L1-L5)
                </CardTitle>
                <CardDescription>Token-efficient code analysis — AST, call graph, CFG, dataflow, slicing</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <Input
                    placeholder="Absolute path to file"
                    value={extractPath}
                    onChange={(e) => setExtractPath(e.target.value)}
                    className="flex-1"
                  />
                  <Button size="sm" onClick={handleExtract} disabled={!extractPath || extractLoading}>
                    {extractLoading ? <Spinner className="mr-2 h-4 w-4" /> : "Extract All"}
                  </Button>
                </div>
                {extractResult && !(extractResult as any).error && (
                  <div className="space-y-2 text-sm">
                    <div className="grid grid-cols-3 gap-2">
                      <div className="border rounded p-2 text-center">
                        <div className="text-lg font-bold text-primary">L1</div>
                        <div className="text-[10px] text-muted-foreground">AST</div>
                      </div>
                      <div className="border rounded p-2 text-center">
                        <div className="text-lg font-bold text-primary">L2</div>
                        <div className="text-[10px] text-muted-foreground">Calls</div>
                      </div>
                      <div className="border rounded p-2 text-center">
                        <div className="text-lg font-bold text-primary">L3</div>
                        <div className="text-[10px] text-muted-foreground">CFG</div>
                      </div>
                    </div>
                    {extractResult && (extractResult as any).summary && (
                      <div className="text-xs text-muted-foreground">
                        Compression: {(extractResult as any).summary.compression_ratio}% &middot;
                        Raw: {(extractResult as any).summary.raw_tokens} tokens &middot;
                        Extracted: {(extractResult as any).summary.total_extracted_tokens} tokens
                      </div>
                    )}
                  </div>
                )}
                {(extractResult as any)?.error && (
                  <p className="text-sm text-red-500">{(extractResult as any).error}</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Saved Graphs</CardTitle>
              </CardHeader>
              <CardContent>
                {graphs.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No graph data yet</p>
                ) : (
                  <div className="space-y-3">
                    {graphs.map((g: any, i) => (
                      <div
                        key={i}
                        className="border rounded-lg p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={async () => {
                          setProjectPath(g.name)
                          const loaded = await api.loadProjectGraph(g.name)
                          setCurrentGraph(loaded.graph)
                          setArchitecture(loaded.architecture)
                        }}
                      >
                        <div className="font-medium text-sm">{g.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {g.nodes} nodes &middot; {g.edges} edges
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {Object.entries(g.layers || {}).map(([layer, count]) => (
                            <Badge key={layer} variant="outline" className="text-[10px]">
                              {layer}: {String(count)}
                            </Badge>
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
