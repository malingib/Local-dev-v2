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
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Skills Library</h1>
          <p className="text-muted-foreground mt-1">Browse available agent skills and capabilities</p>
        </div>

        {/* Search & Filters */}
        <div className="space-y-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search skills..."
              value={searchInput}
              onChange={(e) => handleSearch(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="pl-9"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            {categories.map((cat) => (
              <Button
                key={cat}
                variant={skillCategoryFilter === cat || (cat === "All" && !skillCategoryFilter) ? "default" : "outline"}
                size="sm"
                onClick={() => handleCategoryClick(cat)}
              >
                {cat}
              </Button>
            ))}
          </div>
        </div>

        {/* Skills Grid */}
        {skillsLoading ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : skills.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <Code2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No skills found matching your criteria.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {skills.map((skill) => (
              <Card
                key={skill.id}
                className="cursor-pointer hover:border-primary transition-colors"
                onClick={() => handleSkillClick(skill)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{skill.name}</CardTitle>
                    {skill.category && (
                      <Badge variant="secondary" className="text-xs ml-2 shrink-0">
                        {skill.category}
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                    {skill.description}
                  </p>
                  {skill.tags && skill.tags.length > 0 && (
                    <div className="flex gap-1 flex-wrap">
                      {skill.tags.slice(0, 4).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {skill.tags.length > 4 && (
                        <span className="text-xs text-muted-foreground">+{skill.tags.length - 4}</span>
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
