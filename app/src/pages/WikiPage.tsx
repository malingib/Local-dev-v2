import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useAppStore } from "@/lib/store"
import { Search, Plus, FileText, Trash2, Edit3, Eye } from "lucide-react"

export function WikiPage() {
  const {
    wikiPages, currentWikiPage, wikiSearchResults, wikiLoading,
    fetchWikiPages, selectWikiPage, searchWiki, createWikiPage, updateWikiPage, deleteWikiPage,
  } = useAppStore()

  const [searchQuery, setSearchQuery] = useState("")
  const [showEditor, setShowEditor] = useState(false)
  const [editTitle, setEditTitle] = useState("")
  const [editContent, setEditContent] = useState("")
  const [editTags, setEditTags] = useState("")
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showPreview, setShowPreview] = useState(false)

  useEffect(() => {
    fetchWikiPages()
  }, [fetchWikiPages])

  async function handleSearch(value: string) {
    setSearchQuery(value)
    if (value.trim().length > 0) {
      await searchWiki(value)
    }
  }

  function handleNewPage() {
    setEditingId(null)
    setEditTitle("")
    setEditContent("")
    setEditTags("")
    setShowEditor(true)
    setShowPreview(false)
  }

  function handleEditPage(page: typeof wikiPages[number]) {
    setEditingId(page.id)
    setEditTitle(page.title)
    setEditContent(page.content)
    setEditTags((page.tags || []).join(", "))
    setShowEditor(true)
    setShowPreview(false)
  }

  async function handleSave() {
    if (!editTitle.trim()) return
    const tags = editTags.split(",").map((t) => t.trim()).filter(Boolean)
    if (editingId) {
      await updateWikiPage(editingId, { title: editTitle, content: editContent, tags })
    } else {
      const page = await createWikiPage({ title: editTitle, content: editContent, tags })
      if (page) setEditingId(page.id)
    }
    setShowEditor(false)
  }

  async function handleDelete(id: string) {
    await deleteWikiPage(id)
  }

  function handleSelectPage(page: typeof wikiPages[number]) {
    selectWikiPage(page.id)
  }

  const pageList = searchQuery.trim() ? wikiSearchResults : wikiPages

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">Knowledge Base</h1>
            <p className="text-slate-400 mt-1 font-mono text-sm uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              Collective Intelligence Archive & Wiki
            </p>
          </div>
          <Button
            onClick={handleNewPage}
            className="bg-amber-600 hover:bg-amber-500 text-white font-bold uppercase tracking-widest text-xs px-6"
          >
            <Plus className="h-4 w-4 mr-2" />
            NEW RECORD
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar - Page List */}
          <div className="lg:col-span-1">
            <Card className="glass border-slate-800 bg-slate-900/40">
              <CardHeader className="pb-3 px-4">
                <div className="relative group">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 group-focus-within:text-amber-400 transition-colors" />
                  <Input
                    placeholder="Search archives..."
                    value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="pl-9 bg-slate-950 border-slate-800 text-slate-300 font-mono text-xs focus:ring-amber-500/50"
                  />
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[calc(100vh-280px)]">
                  {wikiLoading && pageList.length === 0 ? (
                    <div className="flex justify-center py-16"><Spinner /></div>
                  ) : pageList.length === 0 ? (
                    <div className="text-center py-20 px-4">
                      <p className="text-[10px] text-slate-600 font-mono uppercase italic tracking-widest">
                        {searchQuery ? "Null results for query" : "No records found in current matrix"}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-0">
                      {pageList.map((page) => (
                        <button
                          key={page.id}
                          className={`w-full text-left px-4 py-4 border-b border-slate-800/50 hover:bg-slate-900/60 transition-all group ${
                            currentWikiPage?.id === page.id ? "bg-amber-500/5 border-l-2 border-l-amber-500" : ""
                          }`}
                          onClick={() => handleSelectPage(page)}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`p-1.5 rounded bg-slate-950 border border-slate-800 group-hover:border-amber-500/50 transition-colors ${currentWikiPage?.id === page.id ? "border-amber-500/50" : ""}`}>
                              <FileText className={`h-3 w-3 ${currentWikiPage?.id === page.id ? "text-amber-400" : "text-slate-500"}`} />
                            </div>
                            <span className={`text-xs font-bold uppercase tracking-wide truncate ${currentWikiPage?.id === page.id ? "text-amber-400" : "text-slate-300 group-hover:text-white"}`}>
                              {page.title}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 mt-2 ml-7">
                            {page.tags?.slice(0, 2).map((tag) => (
                              <Badge key={tag} className="bg-slate-950 text-[8px] font-mono border-slate-800 text-slate-500 px-1.5 py-0">
                                {tag.toUpperCase()}
                              </Badge>
                            ))}
                            <span className="text-[9px] font-mono text-slate-600 ml-auto">
                              {new Date(page.updated_at).toLocaleDateString()}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Main Content - Editor/Preview */}
          <div className="lg:col-span-2">
            {currentWikiPage ? (
              <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
                <div className="h-1 w-full bg-amber-500/50" />
                <CardHeader className="pb-4 px-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-2xl font-black text-white uppercase italic tracking-tight">{currentWikiPage.title}</CardTitle>
                      {currentWikiPage.tags && currentWikiPage.tags.length > 0 && (
                        <div className="flex gap-1.5 mt-2">
                          {currentWikiPage.tags.map((tag) => (
                            <Badge key={tag} className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[9px] font-mono uppercase">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditPage(currentWikiPage)}
                        className="text-slate-400 hover:text-amber-400 hover:bg-amber-500/10 border border-slate-800 hover:border-amber-500/30"
                      >
                        <Edit3 className="h-3 w-3 mr-2" />
                        MODIFY
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(currentWikiPage.id)}
                        className="text-slate-600 hover:text-red-400 hover:bg-red-500/10 border border-slate-800 hover:border-red-500/30"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="px-6">
                  <div className="bg-slate-950/60 rounded-xl border border-slate-800 p-6 min-h-[400px]">
                    <ScrollArea className="h-[calc(100vh-420px)]">
                      <div className="prose prose-invert prose-sm max-w-none text-slate-300 font-sans leading-relaxed">
                        {currentWikiPage.content || <span className="italic text-slate-600 font-mono uppercase tracking-widest text-[10px]">No encoded data in record</span>}
                      </div>
                    </ScrollArea>
                  </div>
                  <div className="mt-4 flex items-center justify-between text-[9px] font-mono text-slate-600 uppercase tracking-widest">
                    <span>RECORD_ID: {currentWikiPage.id.slice(0, 8)}...</span>
                    <span>LAST_MODIFIED: {new Date(currentWikiPage.updated_at).toLocaleString()}</span>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="h-full min-h-[500px] flex flex-col items-center justify-center bg-slate-950/40 rounded-2xl border border-dashed border-slate-800 p-12 text-center group">
                <div className="p-6 rounded-full bg-slate-900 border border-slate-800 mb-6 group-hover:border-amber-500/30 transition-all duration-500">
                  <FileText className="h-12 w-12 text-slate-800 group-hover:text-amber-500/20 transition-all duration-500" />
                </div>
                <h3 className="text-slate-500 font-black uppercase tracking-widest text-lg mb-2">Archive Idle</h3>
                <p className="text-slate-600 font-mono text-[10px] uppercase tracking-tighter max-w-xs mx-auto">
                  Select a knowledge record from the archive or initialize a new neural node to begin documentation.
                </p>
                <Button
                  onClick={handleNewPage}
                  variant="outline"
                  className="mt-8 border-slate-800 text-slate-500 hover:border-amber-500/50 hover:text-amber-400 font-bold uppercase text-[10px] tracking-widest"
                >
                  INITIALIZE NEW RECORD
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={showEditor} onOpenChange={setShowEditor}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Page" : "New Page"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              placeholder="Page title"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
            />
            <Input
              placeholder="Tags (comma separated)"
              value={editTags}
              onChange={(e) => setEditTags(e.target.value)}
            />
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Content (Markdown)</span>
              <Button variant="ghost" size="sm" onClick={() => setShowPreview(!showPreview)}>
                {showPreview ? <Edit3 className="h-4 w-4 mr-1" /> : <Eye className="h-4 w-4 mr-1" />}
                {showPreview ? "Edit" : "Preview"}
              </Button>
            </div>
            {showPreview ? (
              <ScrollArea className="h-[300px] border rounded-md p-4">
                <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm">
                  {editContent || "(empty)"}
                </div>
              </ScrollArea>
            ) : (
              <Textarea
                placeholder="Write your content in markdown..."
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="min-h-[300px] font-mono text-sm"
              />
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditor(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={!editTitle.trim() || wikiLoading}>
              {wikiLoading ? <Spinner className="mr-2" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
