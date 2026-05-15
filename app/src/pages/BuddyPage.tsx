import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { Spinner } from "@/components/ui/spinner"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { useAppStore } from "@/lib/store"
import { Sparkles, Heart, Brain, Zap, Search, MessageCircle } from "lucide-react"

const DEFAULT_OPTIONS = {
  species: ["Fox", "Owl", "Dragon", "Cat", "Robot", "Phoenix"],
  palettes: ["Ember", "Ocean", "Forest", "Storm", "Moonlight", "Aurora"],
  eye_shapes: ["Round", "Slit", "Glowing", "Compound", "Starry", "Digital"],
  accessories: ["Scarf", "Glasses", "Crown", "Wings", "Shield", "Amulet"],
}

export function BuddyPage() {
  const {
    buddy, buddyOptions, buddyLoading,
    fetchBuddy, fetchBuddyOptions, createBuddy, updateBuddy,
  } = useAppStore()

  const [showEdit, setShowEdit] = useState(false)
  const [name, setName] = useState("")
  const [species, setSpecies] = useState("Fox")
  const [palette, setPalette] = useState("Ember")
  const [eyeShape, setEyeShape] = useState("Round")
  const [accessory, setAccessory] = useState("Scarf")

  useEffect(() => {
    fetchBuddy()
    fetchBuddyOptions()
  }, [fetchBuddy, fetchBuddyOptions])

  const options = buddyOptions || DEFAULT_OPTIONS

  function handleOpenEdit() {
    if (!buddy) return
    setName(buddy.name)
    setSpecies(buddy.species)
    setPalette(buddy.palette)
    setEyeShape(buddy.eye_shape)
    setAccessory(buddy.accessories)
    setShowEdit(true)
  }

  async function handleCreate() {
    if (!name.trim()) return
    await createBuddy({
      name: name.trim(),
      species,
      palette,
      eye_shape: eyeShape,
      accessories: accessory,
    })
  }

  async function handleUpdate() {
    if (!name.trim() || !buddy) return
    await updateBuddy({
      name: name.trim(),
      species,
      palette,
      eye_shape: eyeShape,
      accessories: accessory,
    })
    setShowEdit(false)
  }

  const statBars = buddy
    ? [
        { label: "Friendliness", value: buddy.stats.friendliness, icon: Heart },
        { label: "Wisdom", value: buddy.stats.wisdom, icon: Brain },
        { label: "Energy", value: buddy.stats.energy, icon: Zap },
        { label: "Curiosity", value: buddy.stats.curiosity, icon: Search },
      ]
    : []

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Buddy Companion</h1>
          <p className="text-muted-foreground mt-1">Your personal AI companion</p>
        </div>

        {buddyLoading && !buddy ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : buddy ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Avatar Card */}
            <Card className="lg:col-span-1">
              <CardHeader className="text-center">
                <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="h-10 w-10 text-primary" />
                </div>
                <CardTitle className="text-2xl">{buddy.name}</CardTitle>
                <CardDescription>
                  {buddy.species} &middot; {buddy.palette}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <Badge variant="outline">{buddy.species}</Badge>
                  <Badge variant="outline">{buddy.palette}</Badge>
                  <Badge variant="outline">{buddy.eye_shape}</Badge>
                  <Badge variant="outline">{buddy.accessories}</Badge>
                </div>
                {buddy.personality.catchphrase && (
                  <div className="flex items-start gap-2 p-3 bg-muted rounded-lg">
                    <MessageCircle className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                    <p className="text-sm italic">&ldquo;{buddy.personality.catchphrase}&rdquo;</p>
                  </div>
                )}
                <Button variant="outline" className="w-full" onClick={handleOpenEdit}>
                  Edit Visual Traits
                </Button>
              </CardContent>
            </Card>

            {/* Stats & Traits */}
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Stats</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {statBars.map((stat) => (
                    <div key={stat.label}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2 text-sm">
                          <stat.icon className="h-4 w-4" />
                          <span>{stat.label}</span>
                        </div>
                        <span className="text-sm font-medium">{stat.value}%</span>
                      </div>
                      <Progress value={stat.value} className="h-2" />
                    </div>
                  ))}
                </CardContent>
              </Card>

              {buddy.personality.traits && buddy.personality.traits.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Personality Traits</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-2 flex-wrap">
                      {buddy.personality.traits.map((trait: string) => (
                        <Badge key={trait} variant="secondary">{trait}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        ) : (
          /* No Buddy - Hatch Form */
          <Card className="max-w-lg mx-auto">
            <CardHeader className="text-center">
              <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <CardTitle>Hatch a Buddy</CardTitle>
              <CardDescription>Create your AI companion by choosing its traits</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="buddyName">Name</Label>
                <Input
                  id="buddyName"
                  placeholder="Give your buddy a name..."
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Species</Label>
                <Select value={species} onValueChange={setSpecies}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {options.species.map((s: any) => (
                      <SelectItem key={typeof s === 'string' ? s : s.name} value={typeof s === 'string' ? s : s.name}>
                        {typeof s === 'string' ? s : s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Palette</Label>
                <Select value={palette} onValueChange={setPalette}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {options.palettes.map((p) => (
                      <SelectItem key={p} value={p}>{p}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Eye Shape</Label>
                <Select value={eyeShape} onValueChange={setEyeShape}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {options.eye_shapes.map((e) => (
                      <SelectItem key={e} value={e}>{e}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Accessory</Label>
                <Select value={accessory} onValueChange={setAccessory}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {options.accessories.map((a) => (
                      <SelectItem key={a} value={a}>{a}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button className="w-full" onClick={handleCreate} disabled={!name.trim() || buddyLoading}>
                {buddyLoading ? <Spinner className="mr-2" /> : null}
                Hatch Buddy
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit Dialog */}
      <Dialog open={showEdit} onOpenChange={setShowEdit}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Buddy</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Species</Label>
              <Select value={species} onValueChange={setSpecies}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {options.species.map((s: any) => (
                    <SelectItem key={typeof s === 'string' ? s : s.name} value={typeof s === 'string' ? s : s.name}>
                      {typeof s === 'string' ? s : s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Palette</Label>
              <Select value={palette} onValueChange={setPalette}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {options.palettes.map((p) => (
                    <SelectItem key={p} value={p}>{p}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Eye Shape</Label>
              <Select value={eyeShape} onValueChange={setEyeShape}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {options.eye_shapes.map((e) => (
                    <SelectItem key={e} value={e}>{e}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Accessory</Label>
              <Select value={accessory} onValueChange={setAccessory}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {options.accessories.map((a) => (
                    <SelectItem key={a} value={a}>{a}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEdit(false)}>Cancel</Button>
            <Button onClick={handleUpdate} disabled={!name.trim() || buddyLoading}>
              {buddyLoading ? <Spinner className="mr-2" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
