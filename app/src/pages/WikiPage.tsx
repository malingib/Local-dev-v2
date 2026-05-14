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
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Wiki</h1>
            <p className="text-muted-foreground mt-1">Knowledge base documentation</p>
          </div>
          <Button onClick={handleNewPage}>
            <Plus className="h-4 w-4 mr-2" />
            New Page
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar - Page List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader className="pb-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search wiki..."
                    value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[calc(100vh-280px)]">
                  {wikiLoading && pageList.length === 0 ? (
                    <div className="flex justify-center py-8"><Spinner /></div>
                  ) : pageList.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      {searchQuery ? "No matching pages." : "No pages yet. Create one!"}
                    </p>
                  ) : (
                    <div className="space-y-0">
                      {pageList.map((page) => (
                        <button
                          key={page.id}
                          className={`w-full text-left px-4 py-3 border-b last:border-b-0 hover:bg-muted/50 transition-colors ${
                            currentWikiPage?.id === page.id ? "bg-muted" : ""
                          }`}
                          onClick={() => handleSelectPage(page)}
                        >
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                            <span className="text-sm font-medium truncate">{page.title}</span>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            {page.tags?.slice(0, 2).map((tag) => (
                              <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
                            ))}
                            <span className="text-xs text-muted-foreground ml-auto">
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
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">{currentWikiPage.title}</CardTitle>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleEditPage(currentWikiPage)}>
                        <Edit3 className="h-4 w-4 mr-1" />
                        Edit
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => handleDelete(currentWikiPage.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {currentWikiPage.tags && currentWikiPage.tags.length > 0 && (
                    <div className="flex gap-1 mt-2">
                      {currentWikiPage.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
                      ))}
                    </div>
                  )}
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[calc(100vh-380px)]">
                    <div className="prose prose-sm max-w-none text-sm whitespace-pre-wrap">
                      {currentWikiPage.content || "(no content)"}
                    </div>
                  </ScrollArea>
                  <div className="mt-4 text-xs text-muted-foreground">
                    Last modified: {new Date(currentWikiPage.updated_at).toLocaleString()}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-16 text-center text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select a page from the sidebar or create a new one.</p>
                </CardContent>
              </Card>
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
