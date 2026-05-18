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
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">Soul Lab</h1>
            <p className="text-slate-400 mt-1 font-mono text-sm uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
              Agent Identity & Memory Matrix
            </p>
          </div>
          <div className="flex gap-4">
            <div className="px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg backdrop-blur-sm text-right">
              <div className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Identity Integrity</div>
              <div className="text-xl font-mono text-cyan-400 font-bold">98.4%</div>
            </div>
          </div>
        </div>

        {soulLoading && !activeSoul && (
          <div className="flex justify-center py-16"><Spinner /></div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Active Soul Section */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
              <div className="h-1 w-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500" />
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-xl font-bold text-white uppercase tracking-tight">Active Matrix</CardTitle>
                    <CardDescription className="text-slate-400 font-mono text-xs uppercase">Currently loaded personality profile</CardDescription>
                  </div>
                  <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 px-3 py-1 font-mono">
                    SYNCHRONIZED
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {activeSoul ? (
                  <div className="grid gap-4">
                    {Object.entries(FILE_LABELS).map(([key, { label, icon: Icon, desc }]) => (
                      <div key={key} className="group relative flex items-start justify-between p-4 bg-slate-950/40 border border-slate-800/50 rounded-xl hover:border-cyan-500/30 transition-all duration-300">
                        <div className="flex items-start gap-4">
                          <div className="p-2 bg-slate-900 rounded-lg border border-slate-800 group-hover:border-cyan-500/50 transition-colors">
                            <Icon className="h-5 w-5 text-cyan-400" />
                          </div>
                          <div>
                            <div className="font-bold text-slate-200 group-hover:text-white transition-colors flex items-center gap-2 uppercase tracking-wide text-sm">
                              {label}
                              <span className="text-[10px] font-mono text-slate-600 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">MARKDOWN</span>
                            </div>
                            <div className="text-xs text-slate-500 mt-0.5">{desc}</div>
                            <div className="text-[11px] text-slate-400 mt-3 font-mono bg-slate-950/80 p-2 rounded border border-slate-900/50 line-clamp-2 max-w-md italic opacity-70 group-hover:opacity-100 transition-opacity">
                              {(activeSoul as any)[key] ? (activeSoul as any)[key].slice(0, 150) : "// NULL DATA POINT"}
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/10 border border-transparent hover:border-cyan-500/30"
                          onClick={() => handleOpenFile(key)}
                        >
                          <Edit3 className="h-4 w-4 mr-2" />
                          ACCESS
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
                    <p className="text-slate-500 font-mono text-sm">NO ACTIVE MATRIX DETECTED</p>
                    <p className="text-slate-600 text-xs mt-2 uppercase tracking-widest">Select a template to initialize</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Habits & Mistakes Journals */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-green-500/10 rounded border border-green-500/20">
                      <Bookmark className="h-4 w-4 text-green-400" />
                    </div>
                    <CardTitle className="text-lg font-bold text-slate-200 uppercase tracking-tight">Habit Loops</CardTitle>
                  </div>
                  <CardDescription className="font-mono text-[10px] uppercase text-slate-500">Learned behavioral patterns</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-32 flex flex-col items-center justify-center bg-slate-950/20 rounded-lg border border-slate-800/50 border-dashed">
                    <p className="text-[11px] text-slate-600 font-mono text-center px-4">
                      MONITORING INTERACTIONS...<br/>
                      PATTERNS WILL CRYSTALLIZE HERE
                    </p>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-amber-500/10 rounded border border-amber-500/20">
                      <AlertTriangle className="h-4 w-4 text-amber-400" />
                    </div>
                    <CardTitle className="text-lg font-bold text-slate-200 uppercase tracking-tight">Heuristic Errors</CardTitle>
                  </div>
                  <CardDescription className="font-mono text-[10px] uppercase text-slate-500">Corrections & Lessons Learned</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-32 flex flex-col items-center justify-center bg-slate-950/20 rounded-lg border border-slate-800/50 border-dashed">
                    <p className="text-[11px] text-slate-600 font-mono text-center px-4">
                      ZERO ERROR LOGS IN CURRENT SESSION
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Soul Templates Sidebar */}
          <div className="space-y-6">
            <Card className="glass border-slate-800 bg-slate-900/40 sticky top-8">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl font-bold text-white uppercase tracking-tight">Template Library</CardTitle>
                <CardDescription className="text-slate-400 font-mono text-xs uppercase">Archetype initialization</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {displayedTemplates.map((tpl) => (
                  <div
                    key={tpl.id}
                    className={`group cursor-pointer p-4 rounded-xl border transition-all duration-200 ${
                      (activeSoul as any)?.active_template === tpl.id
                        ? "bg-cyan-500/10 border-cyan-500 ring-1 ring-cyan-500/20"
                        : "bg-slate-950/40 border-slate-800 hover:border-slate-600 hover:bg-slate-900/60"
                    }`}
                    onClick={() => handleApplyTemplate(tpl.id)}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <div className="font-bold text-slate-200 group-hover:text-white uppercase tracking-wide text-xs">{tpl.name}</div>
                      {tpl.category && (
                        <span className="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 group-hover:border-slate-700">
                          {tpl.category.toUpperCase()}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 group-hover:text-slate-400 line-clamp-2 leading-relaxed">
                      {tpl.description}
                    </p>
                    {(activeSoul as any)?.active_template === tpl.id && (
                      <div className="mt-2 flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                        <span className="text-[9px] font-mono text-cyan-400 uppercase font-bold">Active Protocol</span>
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
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
