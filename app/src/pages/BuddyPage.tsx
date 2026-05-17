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
import { Sparkles, Heart, Brain, Zap, Search, MessageCircle, Activity, Shield, Cpu } from "lucide-react"

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
        { label: "Neural Empathy", value: buddy.stats.friendliness, icon: Heart, color: "bg-rose-500" },
        { label: "Cognitive Load", value: buddy.stats.wisdom, icon: Brain, color: "bg-blue-500" },
        { label: "Power Output", value: buddy.stats.energy, icon: Zap, color: "bg-amber-500" },
        { label: "Probe Depth", value: buddy.stats.curiosity, icon: Search, color: "bg-emerald-500" },
      ]
    : []

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 swarm-grid">
      <div className="container mx-auto py-8 px-4 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tighter text-white uppercase italic">Companion Core</h1>
            <p className="text-slate-400 mt-1 font-mono text-sm uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Emotional Support Subroutine & Assistant Logic
            </p>
          </div>
          <div className="flex gap-4">
            <div className="px-4 py-1 bg-slate-900 border border-slate-800 rounded flex items-center gap-3">
              <div className="text-[9px] font-bold text-slate-500 uppercase">Sync Status</div>
              <div className="text-[10px] font-mono text-emerald-500 font-bold">STABLE</div>
            </div>
          </div>
        </div>

        {buddyLoading && !buddy ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Spinner className="w-10 h-10 border-slate-500 border-t-white" />
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-[0.3em] animate-pulse">Initializing Unit...</span>
          </div>
        ) : buddy ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Avatar Card */}
            <div className="lg:col-span-4 space-y-6">
              <Card className="glass border-slate-800 bg-slate-900/40 overflow-hidden">
                <div className="h-2 bg-gradient-to-r from-emerald-500 to-blue-500" />
                <CardHeader className="text-center pt-8 pb-4">
                  <div className="relative inline-block mx-auto mb-6">
                    <div className="w-32 h-32 rounded-full bg-slate-950 border-2 border-slate-800 flex items-center justify-center shadow-2xl relative z-10">
                      <Sparkles className="h-14 w-14 text-white" />
                    </div>
                    <div className="absolute -inset-4 bg-emerald-500/20 rounded-full blur-2xl animate-pulse" />
                  </div>
                  <CardTitle className="text-3xl font-black text-white uppercase italic tracking-tight">{buddy.name}</CardTitle>
                  <CardDescription className="font-mono text-[10px] uppercase tracking-widest text-slate-500 mt-1">
                    {buddy.species} Class &middot; {buddy.palette} Matrix
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 bg-slate-950/60 border border-slate-800 rounded">
                      <div className="text-[8px] font-bold text-slate-600 uppercase">Optic Type</div>
                      <div className="text-[10px] font-mono text-slate-300">{buddy.eye_shape}</div>
                    </div>
                    <div className="p-2 bg-slate-950/60 border border-slate-800 rounded">
                      <div className="text-[8px] font-bold text-slate-600 uppercase">Module</div>
                      <div className="text-[10px] font-mono text-slate-300">{buddy.accessories}</div>
                    </div>
                  </div>

                  {buddy.personality.catchphrase && (
                    <div className="relative group">
                      <div className="absolute -left-2 top-0 bottom-0 w-0.5 bg-slate-700 group-hover:bg-emerald-500 transition-colors" />
                      <div className="pl-4 py-1">
                        <MessageCircle className="h-3 w-3 text-slate-600 mb-2" />
                        <p className="text-xs italic text-slate-400 leading-relaxed font-serif">&ldquo;{buddy.personality.catchphrase}&rdquo;</p>
                      </div>
                    </div>
                  )}

                  <Button
                    variant="outline"
                    className="w-full bg-slate-950 border-slate-800 text-slate-400 hover:text-white hover:border-slate-500 uppercase text-[10px] font-bold tracking-widest h-10"
                    onClick={handleOpenEdit}
                  >
                    Recalibrate Visuals
                  </Button>
                </CardContent>
              </Card>

              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="pb-3">
                  <CardTitle className="text-[11px] font-black uppercase text-slate-500 flex items-center gap-2 tracking-widest">
                    <Shield className="w-3 h-3" /> Core Integrity
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-slate-400 uppercase">Operational Mode</span>
                    <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[9px] font-mono uppercase">ACTIVE</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-slate-400 uppercase">Logic Gate</span>
                    <span className="text-[10px] font-mono text-slate-200">XOR-99-ALPHA</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Stats & Traits */}
            <div className="lg:col-span-8 space-y-8">
              <Card className="glass border-slate-800 bg-slate-900/40">
                <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800 pb-4 mb-4">
                  <div>
                    <CardTitle className="text-white uppercase font-bold tracking-tight">Telemetry Readout</CardTitle>
                    <CardDescription className="text-slate-500 font-mono text-xs uppercase italic">Real-time companion performance metrics</CardDescription>
                  </div>
                  <Activity className="h-5 w-5 text-slate-700" />
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8 pt-4">
                  {statBars.map((stat) => (
                    <div key={stat.label} className="group">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3 text-sm">
                          <div className="p-1.5 bg-slate-950 border border-slate-800 rounded group-hover:border-slate-500 transition-colors">
                            <stat.icon className="h-4 w-4 text-slate-400 group-hover:text-white" />
                          </div>
                          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">{stat.label}</span>
                        </div>
                        <span className="text-xs font-mono font-bold text-slate-200">{stat.value}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-950 border border-slate-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${stat.color} transition-all duration-1000 ease-out`}
                          style={{ width: `${stat.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {buddy.personality.traits && buddy.personality.traits.length > 0 && (
                <Card className="glass border-slate-800 bg-slate-900/40">
                  <CardHeader>
                    <CardTitle className="text-white uppercase font-bold tracking-tight">Neural Directives</CardTitle>
                    <CardDescription className="text-slate-500 font-mono text-xs uppercase">Primary personality weighting modules</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-3 flex-wrap">
                      {buddy.personality.traits.map((trait: string) => (
                        <div key={trait} className="px-4 py-2 bg-slate-950 border border-slate-800 rounded-full flex items-center gap-2 group hover:border-slate-500 transition-all">
                          <Cpu className="w-3 h-3 text-slate-600 group-hover:text-emerald-500" />
                          <span className="text-[10px] font-mono text-slate-300 uppercase tracking-widest">{trait}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card className="border-dashed border-slate-800 bg-transparent">
                <CardContent className="py-8 text-center">
                  <p className="text-[10px] font-mono text-slate-600 uppercase tracking-[0.2em] italic">
                    Unit {buddy.name} is synchronized with your workflow. Terminal support is enabled.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          /* No Buddy - Hatch Form */
          <Card className="max-w-xl mx-auto glass border-slate-800 bg-slate-900/60 shadow-2xl overflow-hidden mt-12">
            <div className="h-1 bg-gradient-to-r from-emerald-500 via-blue-500 to-emerald-500 animate-pulse" />
            <CardHeader className="text-center pt-10 pb-6">
              <div className="relative inline-block mx-auto mb-6">
                <div className="w-24 h-24 rounded-full bg-slate-950 border border-slate-800 flex items-center justify-center relative z-10">
                  <Sparkles className="h-10 w-10 text-emerald-500 animate-pulse" />
                </div>
                <div className="absolute inset-0 bg-emerald-500/10 rounded-full blur-xl scale-150" />
              </div>
              <CardTitle className="text-3xl font-black text-white uppercase italic">Initialize Companion</CardTitle>
              <CardDescription className="font-mono text-xs uppercase tracking-widest text-slate-500">Configure your assistant's neural blueprint</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 px-10 pb-10">
              <div className="space-y-2">
                <Label htmlFor="buddyName" className="text-[10px] font-bold text-slate-500 uppercase ml-1">ID Designation</Label>
                <Input
                  id="buddyName"
                  placeholder="ENTER UNIT NAME..."
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-slate-200 font-mono text-sm uppercase tracking-widest focus:ring-emerald-500/50 h-12"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Biological Template</Label>
                  <Select value={species} onValueChange={setSpecies}>
                    <SelectTrigger className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase h-10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                      {options.species.map((s: any) => (
                        <SelectItem key={typeof s === 'string' ? s : s.name} value={typeof s === 'string' ? s : s.name} className="text-[10px] font-mono uppercase">
                          {typeof s === 'string' ? s : s.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Spectral Palette</Label>
                  <Select value={palette} onValueChange={setPalette}>
                    <SelectTrigger className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase h-10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                      {options.palettes.map((p) => (
                        <SelectItem key={p} value={p} className="text-[10px] font-mono uppercase">{p}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Optic Array</Label>
                  <Select value={eyeShape} onValueChange={setEyeShape}>
                    <SelectTrigger className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase h-10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                      {options.eye_shapes.map((e) => (
                        <SelectItem key={e} value={e} className="text-[10px] font-mono uppercase">{e}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Integrated Module</Label>
                  <Select value={accessory} onValueChange={setAccessory}>
                    <SelectTrigger className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase h-10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                      {options.accessories.map((a) => (
                        <SelectItem key={a} value={a} className="text-[10px] font-mono uppercase">{a}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-black uppercase text-[12px] tracking-[0.2em] h-14 mt-4 shadow-lg shadow-emerald-950/50"
                onClick={handleCreate}
                disabled={!name.trim() || buddyLoading}
              >
                {buddyLoading ? <Spinner className="mr-2" /> : "BEGIN SEQUENCING"}
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit Dialog */}
      <Dialog open={showEdit} onOpenChange={setShowEdit}>
        <DialogContent className="bg-slate-900 border-slate-800 text-slate-50">
          <DialogHeader>
            <DialogTitle className="text-white uppercase font-bold tracking-tight">Recalibrate Unit</DialogTitle>
            <CardDescription className="font-mono text-[10px] uppercase">Modifier matrix for unit visuals</CardDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-[10px] font-bold text-slate-500 uppercase">Designation</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} className="bg-slate-950 border-slate-800 text-[11px] font-mono" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-[10px] font-bold text-slate-500 uppercase">Class</Label>
                <Select value={species} onValueChange={setSpecies}>
                  <SelectTrigger className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase h-10"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                    {options.species.map((s: any) => (
                      <SelectItem key={typeof s === 'string' ? s : s.name} value={typeof s === 'string' ? s : s.name} className="text-[10px] font-mono uppercase">
                        {typeof s === 'string' ? s : s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-[10px] font-bold text-slate-500 uppercase">Palette</Label>
                <Select value={palette} onValueChange={setPalette}>
                  <SelectTrigger className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase h-10"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                    {options.palettes.map((p) => (
                      <SelectItem key={p} value={p} className="text-[10px] font-mono uppercase">{p}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-[10px] font-bold text-slate-500 uppercase">Optics</Label>
                <Select value={eyeShape} onValueChange={setEyeShape}>
                  <SelectTrigger className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase h-10"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                    {options.eye_shapes.map((e) => (
                      <SelectItem key={e} value={e} className="text-[10px] font-mono uppercase">{e}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-[10px] font-bold text-slate-500 uppercase">Module</Label>
                <Select value={accessory} onValueChange={setAccessory}>
                  <SelectTrigger className="bg-slate-950 border-slate-800 text-[11px] font-mono uppercase h-10"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                    {options.accessories.map((a) => (
                      <SelectItem key={a} value={a} className="text-[10px] font-mono uppercase">{a}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="ghost" onClick={() => setShowEdit(false)} className="text-[10px] font-bold uppercase text-slate-500">ABORT</Button>
            <Button onClick={handleUpdate} disabled={!name.trim() || buddyLoading} className="bg-slate-100 hover:bg-white text-slate-950 font-black uppercase text-[10px] tracking-widest px-8">
              {buddyLoading ? <Spinner className="mr-2" /> : "OVERWRITE BLUEPRINT"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
