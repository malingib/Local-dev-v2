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
    if (score > 0.9) return "text-green-500"
    if (score > 0.7) return "text-yellow-500"
    return "text-muted-foreground"
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center gap-3 mb-8">
          <Search className="h-7 w-7" />
          <div>
            <h1 className="text-3xl font-bold">File Search</h1>
            <p className="text-muted-foreground">Fast file & symbol search — inspired by fff.nvim</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Search</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="/path/to/project (leave empty for current)"
                    value={root}
                    onChange={(e) => setRoot(e.target.value)}
                    className="flex-1"
                  />
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder={searchType === "symbols" ? "Search symbol name..." : "Search files..."}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    className="flex-1"
                  />
                  <Button onClick={handleSearch} disabled={!query.trim() || searchLoading}>
                    {searchLoading ? <Spinner className="mr-2 h-4 w-4" /> : <Search className="mr-2 h-4 w-4" />}
                    Search
                  </Button>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <div className="flex gap-1">
                    <Button size="sm" variant={searchType === "files" ? "default" : "outline"} onClick={() => setSearchType("files")}>
                      <FileText className="h-3 w-3 mr-1" /> Files
                    </Button>
                    <Button size="sm" variant={searchType === "symbols" ? "default" : "outline"} onClick={() => { setSearchType("symbols"); clearSearch() }}>
                      <Code className="h-3 w-3 mr-1" /> Symbols
                    </Button>
                  </div>
                  {searchType === "files" && (
                    <div className="flex gap-1">
                      {(["fuzzy", "path", "content"] as const).map((m) => (
                        <Button key={m} size="sm" variant={mode === m ? "secondary" : "ghost"} onClick={() => setMode(m)}>
                          {m}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {searchResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">
                    Results ({searchResults.length}) — mode: {searchMode}, query: "{searchQuery}"
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {searchResults.map((r, i) => (
                      <div key={i} className="flex items-center justify-between text-sm border-b pb-2 last:border-0">
                        <div className="flex-1 min-w-0">
                          <span className="font-mono text-xs truncate block">{r.path}</span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Badge variant="outline" className="text-[10px]">{r.mode}</Badge>
                          <span className={`font-mono text-xs ${getSeverityColor(r.score)}`}>{r.score.toFixed(3)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {searchSymbolResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Symbol Results ({searchSymbolResults.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {searchSymbolResults.map((r, i) => (
                      <div key={i} className="flex items-center justify-between text-sm border-b pb-2 last:border-0">
                        <div className="flex-1 min-w-0">
                          <span className="font-mono text-xs">{r.symbol}</span>
                          <span className="text-muted-foreground text-xs ml-2">in {r.path}:{r.line}</span>
                        </div>
                        <Badge variant="outline" className="text-[10px] shrink-0">symbol</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {!searchResults.length && !searchSymbolResults.length && searchQuery && !searchLoading && (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  No results for "{searchQuery}"
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Recent Files
                </CardTitle>
              </CardHeader>
              <CardContent>
                {recentFiles.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No recent files yet</p>
                ) : (
                  <div className="space-y-1 max-h-60 overflow-y-auto">
                    {recentFiles.map((f, i) => (
                      <div key={i} className="text-xs truncate flex items-center gap-1">
                        <FileText className="h-3 w-3 shrink-0 text-muted-foreground" />
                        <span className="truncate">{f.path}</span>
                        <span className="text-muted-foreground shrink-0">({f.access_count}x)</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Hash className="h-4 w-4" />
                  Context Stats
                </CardTitle>
              </CardHeader>
              <CardContent>
                {contextStats ? (
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Savings</span>
                      <span className="font-mono">{contextStats.savings_percent}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Sandbox calls</span>
                      <span className="font-mono">{contextStats.sandbox_calls}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Raw chars</span>
                      <span className="font-mono">{contextStats.total_raw_chars.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Compressed</span>
                      <span className="font-mono">{contextStats.total_compressed_chars.toLocaleString()}</span>
                    </div>
                    {Object.keys(contextStats.savings_by_tool || {}).length > 0 && (
                      <>
                        <div className="text-xs font-medium mt-2 text-muted-foreground">By tool:</div>
                        {Object.entries(contextStats.savings_by_tool || {}).map(([tool, stats]) => (
                          <div key={tool} className="flex justify-between pl-2">
                            <span className="text-muted-foreground">{tool}</span>
                            <span className="font-mono">{stats.calls}x</span>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No stats yet</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
