import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { useAppStore } from "@/lib/store"
import { Search, FileText, Code, Clock, Hash } from "lucide-react"

export function SearchPage() {
  const {
    searchResults, searchSymbolResults, recentFiles,
    searchLoading, searchQuery, searchMode,
    searchFiles, searchSymbols, fetchRecentFiles, clearSearch,
    fetchContextStats, contextStats,
  } = useAppStore()

  const [root, setRoot] = useState("")
  const [query, setQuery] = useState("")
  const [mode, setMode] = useState<"fuzzy" | "path" | "content">("fuzzy")
  const [searchType, setSearchType] = useState<"files" | "symbols">("files")

  useEffect(() => {
    fetchRecentFiles(root)
    fetchContextStats()
  }, [])

  function handleSearch() {
    if (!query.trim()) return
    if (searchType === "symbols") {
      searchSymbols(root, query)
    } else {
      searchFiles(root, query, mode)
    }
  }

  function getSeverityColor(score: number) {
    if (score > 0.9) return "text-emerald-400"
    if (score > 0.7) return "text-amber-400"
    return "text-slate-500"
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">Deep Search</h1>
            <p className="text-slate-400 mt-1 font-mono text-sm uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              High-Velocity File & Symbol Discovery
            </p>
          </div>
          <div className="px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg backdrop-blur-sm flex gap-6">
            <div className="text-right">
              <div className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Indexing Status</div>
              <div className="text-xl font-mono text-emerald-400 font-bold uppercase">Ready</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3 space-y-6">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-4">
                <CardTitle className="text-white uppercase tracking-tight font-bold flex items-center gap-2">
                  <Search className="h-5 w-5 text-emerald-400" />
                  Global Query
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Search Root</label>
                    <Input
                      placeholder="/path/to/project (defaults to workspace)"
                      value={root}
                      onChange={(e) => setRoot(e.target.value)}
                      className="bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs focus:ring-emerald-500/50"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Query Mode</label>
                    <div className="flex gap-1 p-1 bg-slate-950 rounded-md border border-slate-800">
                      {(["fuzzy", "path", "content"] as const).map((m) => (
                        <button
                          key={m}
                          onClick={() => setMode(m)}
                          className={`flex-1 text-[10px] font-bold uppercase py-1 rounded transition-colors ${
                            mode === m ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "text-slate-600 hover:text-slate-400"
                          }`}
                        >
                          {m}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="relative group">
                  <Input
                    placeholder={searchType === "symbols" ? "Enter symbol identifier (e.g. handleUpdate)..." : "Enter file path or glob pattern..."}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    className="h-12 pl-4 pr-32 bg-slate-950 border-slate-800 text-emerald-50 font-mono text-sm focus:ring-emerald-500/50"
                  />
                  <div className="absolute right-1.5 top-1.5 bottom-1.5 flex gap-1.5">
                    <Button
                      onClick={handleSearch}
                      disabled={!query.trim() || searchLoading}
                      className="h-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold uppercase tracking-widest text-[10px] px-4"
                    >
                      {searchLoading ? <Spinner className="h-3 w-3" /> : "Execute"}
                    </Button>
                  </div>
                </div>

                <div className="flex gap-3 items-center">
                  <div className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">Scope:</div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSearchType("files")}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-[10px] font-bold uppercase transition-all ${
                        searchType === "files" ? "bg-emerald-500/10 border-emerald-500 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.1)]" : "bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-700"
                      }`}
                    >
                      <FileText className="h-3 w-3" /> Files
                    </button>
                    <button
                      onClick={() => { setSearchType("symbols"); clearSearch() }}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-[10px] font-bold uppercase transition-all ${
                        searchType === "symbols" ? "bg-emerald-500/10 border-emerald-500 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.1)]" : "bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-700"
                      }`}
                    >
                      <Code className="h-3 w-3" /> Symbols
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {searchResults.length > 0 && (
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-mono uppercase text-slate-400">
                      Discovery Results ({searchResults.length}) — <span className="text-emerald-500">{searchMode.toUpperCase()}</span>
                    </CardTitle>
                    <Badge variant="outline" className="text-[10px] font-mono border-slate-800 text-slate-500 bg-slate-950">Q: {searchQuery}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1.5 max-h-[500px] overflow-y-auto scrollbar-hide pr-2">
                    {searchResults.map((r, i) => (
                      <div key={i} className="group flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-800/50 rounded-lg hover:border-emerald-500/30 hover:bg-slate-900/50 transition-all duration-200">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800 group-hover:border-emerald-500/50 transition-colors">
                            <FileText className="h-3 w-3 text-slate-500 group-hover:text-emerald-400" />
                          </div>
                          <span className="font-mono text-[11px] text-slate-300 group-hover:text-white truncate block">{r.path}</span>
                        </div>
                        <div className="flex items-center gap-4 shrink-0 pl-4">
                          <div className="text-[10px] font-mono text-slate-600 uppercase">{r.mode}</div>
                          <div className="w-16 h-1.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                            <div
                              className="h-full bg-emerald-500/50"
                              style={{ width: `${Math.min(100, r.score * 100)}%` }}
                            />
                          </div>
                          <span className={`font-mono text-[10px] font-bold w-10 text-right ${getSeverityColor(r.score)}`}>{r.score.toFixed(3)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {searchSymbolResults.length > 0 && (
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-mono uppercase text-slate-400">Symbol Results ({searchSymbolResults.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1.5 max-h-[500px] overflow-y-auto scrollbar-hide pr-2">
                    {searchSymbolResults.map((r, i) => (
                      <div key={i} className="group flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-800/50 rounded-lg hover:border-emerald-500/30 hover:bg-slate-900/50 transition-all duration-200">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800 group-hover:border-emerald-500/50 transition-colors">
                            <Code className="h-3 w-3 text-emerald-500/50 group-hover:text-emerald-400" />
                          </div>
                          <div className="min-w-0">
                            <span className="font-mono text-[11px] font-bold text-slate-200 group-hover:text-emerald-400 transition-colors block">{r.symbol}</span>
                            <span className="text-[10px] text-slate-500 font-mono italic">in {r.path}:{r.line}</span>
                          </div>
                        </div>
                        <Badge variant="outline" className="text-[8px] font-bold uppercase border-slate-800 text-slate-600 bg-slate-950 px-1.5">Symbol</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {!searchResults.length && !searchSymbolResults.length && searchQuery && !searchLoading && (
              <div className="text-center py-20 bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
                <Search className="h-10 w-10 text-slate-800 mx-auto mb-4" />
                <p className="text-slate-500 font-mono text-sm uppercase tracking-widest italic">Null pointer returned for "{searchQuery}"</p>
                <p className="text-slate-600 text-[10px] mt-2">Adjust query parameters and re-execute</p>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-bold text-slate-200 uppercase tracking-widest flex items-center gap-2">
                  <Clock className="h-4 w-4 text-emerald-400" />
                  Recent Cache
                </CardTitle>
              </CardHeader>
              <CardContent>
                {recentFiles.length === 0 ? (
                  <div className="text-center py-6 text-slate-700 text-[10px] uppercase font-mono italic">Empty Stack</div>
                ) : (
                  <div className="space-y-1 max-h-60 overflow-y-auto scrollbar-hide">
                    {recentFiles.map((f, i) => (
                      <div key={i} className="group flex items-center gap-2 p-1.5 rounded hover:bg-slate-900/60 transition-colors">
                        <FileText className="h-3 w-3 shrink-0 text-slate-600 group-hover:text-emerald-500" />
                        <span className="text-[10px] font-mono text-slate-500 group-hover:text-slate-300 truncate">{f.path.split('/').pop()}</span>
                        <span className="text-[9px] font-bold text-slate-800 ml-auto">{f.access_count}X</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-bold text-slate-200 uppercase tracking-widest flex items-center gap-2">
                  <Hash className="h-4 w-4 text-emerald-400" />
                  Context Efficiency
                </CardTitle>
              </CardHeader>
              <CardContent>
                {contextStats ? (
                  <div className="space-y-4">
                    <div className="flex flex-col items-center">
                      <div className="text-3xl font-black text-emerald-400 font-mono leading-none">{contextStats.savings_percent}%</div>
                      <div className="text-[9px] font-bold text-slate-600 uppercase mt-1 tracking-tighter italic">Tokens Saved</div>
                    </div>

                    <div className="space-y-2 border-t border-slate-800/50 pt-3">
                      <div className="flex justify-between text-[10px] font-mono">
                        <span className="text-slate-500 uppercase">Sandbox</span>
                        <span className="text-slate-200">{contextStats.sandbox_calls} OPS</span>
                      </div>
                      <div className="flex justify-between text-[10px] font-mono">
                        <span className="text-slate-500 uppercase">Input</span>
                        <span className="text-slate-200">{(contextStats.total_raw_chars / 1024).toFixed(1)} KB</span>
                      </div>
                      <div className="flex justify-between text-[10px] font-mono">
                        <span className="text-slate-500 uppercase">Compressed</span>
                        <span className="text-emerald-400 font-bold">{(contextStats.total_compressed_chars / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>

                    {Object.keys(contextStats.savings_by_tool || {}).length > 0 && (
                      <div className="space-y-1.5 border-t border-slate-800/50 pt-3">
                        <div className="text-[9px] font-bold text-slate-600 uppercase mb-2">Efficiency by tool</div>
                        {Object.entries(contextStats.savings_by_tool || {}).map(([tool, stats]) => (
                          <div key={tool} className="flex justify-between items-center bg-slate-950/40 p-1.5 rounded border border-slate-800/30">
                            <span className="text-[9px] font-mono text-slate-400 uppercase">{tool}</span>
                            <span className="text-[10px] font-mono text-emerald-500/70 font-bold">{stats.calls}X</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-6 text-slate-700 text-[10px] uppercase font-mono italic">No Telemetry</div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
