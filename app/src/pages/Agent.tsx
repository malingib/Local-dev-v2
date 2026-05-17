import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useAppStore } from "@/lib/store"
import { BookOpen, User, Bot, Edit3, Bookmark, AlertTriangle } from "lucide-react"

const SOUL_TEMPLATES = [
  { id: "default", name: "Default", description: "Balanced general-purpose agent", category: "General" },
  { id: "creative", name: "Creative", description: "Imaginative and artistic coding companion", category: "Creative" },
  { id: "teacher", name: "Teacher", description: "Educational focus with detailed explanations", category: "Education" },
  { id: "researcher", name: "Researcher", description: "Deep analysis and research-oriented", category: "Research" },
  { id: "pair-programmer", name: "Pair Programmer", description: "Collaborative coding partner", category: "Development" },
  { id: "devops", name: "DevOps", description: "Infrastructure and deployment focused", category: "DevOps" },
  { id: "security", name: "Security", description: "Security-first mindset for code review", category: "Security" },
  { id: "helper", name: "Helper", description: "Friendly assistant for everyday tasks", category: "General" },
  { id: "mentor", name: "Mentor", description: "Guiding you through best practices", category: "Education" },
  { id: "engineer", name: "Engineer", description: "Software engineering best practices", category: "Development" },
  { id: "writer", name: "Writer", description: "Documentation and content creation", category: "Creative" },
  { id: "analyst", name: "Analyst", description: "Data-driven analytical approach", category: "Research" },
]

const FILE_LABELS: Record<string, { label: string; icon: typeof BookOpen; desc: string }> = {
  soul: { label: "SOUL.md", icon: Bot, desc: "Core identity and personality" },
  user: { label: "USER.md", icon: User, desc: "User preferences and context" },
  agents: { label: "AGENTS.md", icon: BookOpen, desc: "Agent capabilities and tools" },
  habits: { label: "habits.md", icon: Bookmark, desc: "Habits and patterns journal" },
  mistakes: { label: "mistakes.md", icon: AlertTriangle, desc: "Mistakes and lessons learned" },
}

export function Agent() {
  const {
    activeSoul, soulTemplates, soulLoading, soulEditing,
    fetchActiveSoul, fetchSoulTemplates, applySoulTemplate,
    openSoulFile, saveSoulFile, closeSoulEditor,
  } = useAppStore()

  const [editContent, setEditContent] = useState("")

  useEffect(() => {
    fetchActiveSoul()
    fetchSoulTemplates()
  }, [fetchActiveSoul, fetchSoulTemplates])

  async function handleApplyTemplate(id: string) {
    await applySoulTemplate(id)
  }

  async function handleSaveEdit() {
    if (!soulEditing) return
    await saveSoulFile(soulEditing.type, editContent)
  }

  async function handleOpenFile(type: string) {
    await openSoulFile(type)
    setEditContent(useAppStore.getState().soulEditing?.content || "")
  }

  const displayedTemplates = soulTemplates.length > 0 ? soulTemplates : SOUL_TEMPLATES

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Agent Soul</h1>
          <p className="text-muted-foreground mt-1">Manage the agent's identity, personality, and memory</p>
        </div>

        {soulLoading && !activeSoul && (
          <div className="flex justify-center py-16"><Spinner /></div>
        )}

        {/* Active Soul Section */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Active Soul</CardTitle>
                <CardDescription>Currently loaded personality profile</CardDescription>
              </div>
              <Badge variant="outline">
                active
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {activeSoul ? (
              <div className="space-y-4">
                {Object.entries(FILE_LABELS).map(([key, { label, icon: Icon, desc }]) => (
                  <div key={key} className="flex items-start justify-between p-3 border rounded-lg">
                    <div className="flex items-start gap-3">
                      <Icon className="h-5 w-5 mt-0.5 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{label}</div>
                        <div className="text-sm text-muted-foreground">{desc}</div>
                        <div className="text-xs text-muted-foreground mt-1 font-mono line-clamp-2">
                          {(activeSoul as any)[key] ? (activeSoul as any)[key].slice(0, 120) : "(empty)"}
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => handleOpenFile(key)}>
                      <Edit3 className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-8">No active soul loaded. Select a template below.</p>
            )}
          </CardContent>
        </Card>

        {/* Soul Templates */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Soul Templates</CardTitle>
            <CardDescription>Choose a predefined personality for the agent</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {displayedTemplates.map((tpl) => (
                <Card
                  key={tpl.id}
                  className={`cursor-pointer transition-colors hover:border-primary ${
                    (activeSoul as any)?.active_template === tpl.id ? "border-primary ring-1 ring-primary" : ""
                  }`}
                  onClick={() => handleApplyTemplate(tpl.id)}
                >
                  <CardHeader className="p-4 pb-2">
                    <CardTitle className="text-sm">{tpl.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 pt-0">
                    <p className="text-xs text-muted-foreground">{tpl.description}</p>
                    {tpl.category && (
                      <Badge variant="outline" className="mt-2 text-xs">
                        {tpl.category}
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Habits & Mistakes Journals */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bookmark className="h-5 w-5 text-muted-foreground" />
                <CardTitle className="text-lg">Habits Journal</CardTitle>
              </div>
              <CardDescription>Learned behaviors and positive patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground text-center py-8">
                Habits will appear here as the agent learns from interactions.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-muted-foreground" />
                <CardTitle className="text-lg">Mistakes Journal</CardTitle>
              </div>
              <CardDescription>Errors and corrections to learn from</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground text-center py-8">
                Mistakes will appear here as the agent logs corrections.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Soul File Editor Dialog */}
      <Dialog open={!!soulEditing} onOpenChange={(open) => { if (!open) closeSoulEditor() }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Editing {soulEditing ? FILE_LABELS[soulEditing.type]?.label || soulEditing.type : ""}
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[400px]">
            <Textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="min-h-[350px] font-mono text-sm"
              placeholder="Enter markdown content..."
            />
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={closeSoulEditor}>Cancel</Button>
            <Button onClick={handleSaveEdit} disabled={soulLoading}>
              {soulLoading ? <Spinner className="mr-2" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
