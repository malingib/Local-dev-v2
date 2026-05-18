import { useState, useEffect, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useAppStore } from "@/lib/store"
import { Search, Code2 } from "lucide-react"

export function SkillsPage() {
  const {
    skills, skillsLoading, skillCategoryFilter,
    fetchSkills, setSkillSearch, setSkillCategoryFilter,
  } = useAppStore()

  const [selectedSkill, setSelectedSkill] = useState<typeof skills[number] | null>(null)
  const [searchInput, setSearchInput] = useState("")

  useEffect(() => {
    fetchSkills()
  }, [fetchSkills])

  const categories = useMemo(() => {
    const cats = new Set(skills.map((s) => s.category).filter(Boolean))
    return ["All", ...Array.from(cats)]
  }, [skills])

  function handleSearch(value: string) {
    setSearchInput(value)
  }

  function handleSearchKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      setSkillSearch(searchInput)
    }
  }

  function handleCategoryClick(cat: string) {
    setSkillCategoryFilter(cat === "All" ? "" : cat)
  }

  function handleSkillClick(skill: typeof skills[number]) {
    setSelectedSkill(skill)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">Toolbox</h1>
            <p className="text-slate-400 mt-1 font-mono text-sm uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
              Agent Capability Matrix & Functional Library
            </p>
          </div>
          <div className="px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg backdrop-blur-sm">
            <div className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Available Skills</div>
            <div className="text-xl font-mono text-blue-400 font-bold">{skills.length} MODULES</div>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="space-y-4 mb-8">
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500 group-focus-within:text-blue-400 transition-colors" />
            <Input
              placeholder="Search functional modules..."
              value={searchInput}
              onChange={(e) => handleSearch(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="pl-12 h-14 bg-slate-900/40 border-slate-800 text-white font-mono text-sm focus:ring-blue-500/50 backdrop-blur-md rounded-2xl"
            />
          </div>
          <div className="flex gap-2 flex-wrap items-center">
            <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mr-2">Filter Matrix:</span>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => handleCategoryClick(cat)}
                className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all border ${
                  skillCategoryFilter === cat || (cat === "All" && !skillCategoryFilter)
                    ? "bg-blue-600 border-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.2)]"
                    : "bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-600 hover:text-slate-300"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Skills Grid */}
        {skillsLoading ? (
          <div className="flex justify-center py-20"><Spinner /></div>
        ) : skills.length === 0 ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-slate-950/40 rounded-2xl border border-dashed border-slate-800 p-12 text-center">
            <Code2 className="h-12 w-12 text-slate-800 mb-4" />
            <h3 className="text-slate-500 font-black uppercase tracking-widest text-lg mb-2">No Modules Found</h3>
            <p className="text-slate-600 font-mono text-[10px] uppercase tracking-tighter">Your query returned zero matches in the current functional library.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {skills.map((skill) => (
              <Card
                key={skill.id}
                className="group relative cursor-pointer glass border-slate-800 bg-slate-900/40 hover:border-blue-500/50 transition-all duration-300 overflow-hidden"
                onClick={() => handleSkillClick(skill)}
              >
                <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-100 transition-opacity">
                  <Code2 className="h-4 w-4 text-blue-400" />
                </div>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between pr-4">
                    <CardTitle className="text-sm font-bold text-slate-200 group-hover:text-white uppercase tracking-tight transition-colors">
                      {skill.name}
                    </CardTitle>
                  </div>
                  {skill.category && (
                    <div className="text-[9px] font-mono font-bold text-blue-500 uppercase tracking-tighter">
                      {skill.category}
                    </div>
                  )}
                </CardHeader>
                <CardContent>
                  <p className="text-[11px] text-slate-500 group-hover:text-slate-400 line-clamp-2 mb-4 leading-relaxed font-sans">
                    {skill.description}
                  </p>
                  {skill.tags && skill.tags.length > 0 && (
                    <div className="flex gap-1.5 flex-wrap">
                      {skill.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="text-[8px] font-mono text-slate-600 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 uppercase tracking-tighter group-hover:border-slate-700">
                          {tag}
                        </span>
                      ))}
                      {skill.tags.length > 3 && (
                        <span className="text-[8px] font-mono text-slate-700">+{skill.tags.length - 3}</span>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Skill Detail Dialog */}
      <Dialog open={!!selectedSkill} onOpenChange={(open) => { if (!open) setSelectedSkill(null) }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedSkill?.name}
              {selectedSkill?.category && (
                <Badge variant="secondary" className="text-xs">{selectedSkill.category}</Badge>
              )}
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[400px]">
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">{selectedSkill?.description}</p>
              {(selectedSkill as any)?.details && (
                <p className="text-sm">{(selectedSkill as any).details}</p>
              )}
              {selectedSkill?.tags && selectedSkill.tags.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Tags</h4>
                  <div className="flex gap-1 flex-wrap">
                    {selectedSkill.tags.map((tag) => (
                      <Badge key={tag} variant="outline">{tag}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  )
}
