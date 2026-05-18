import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Bot, Send, Terminal, Users, Settings2, Activity,
  Network, Cpu, Zap, Radio, MessageSquare, Shield,
  Layers, ChevronRight, Search
} from "lucide-react"
import * as api from "@/lib/api"
import { VisualSwarmGraph } from "@/components/VisualSwarmGraph"
import { cn } from "@/lib/utils"

export function SwarmDashboard() {
  const [status, setStatus] = useState<any>(null)
  const [agents, setAgents] = useState<any[]>([])
  const [activity, setActivity] = useState<any[]>([])
  const [taskDesc, setTaskDesc] = useState("")
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const fetchStatus = async () => {
    try {
      const data = await api.getSwarmStatus()
      setStatus(data)
    } catch (e) {
      console.error("Failed to fetch swarm status", e)
    }
  }

  const fetchAgents = async () => {
    try {
      const data = await api.listSwarmAgents()
      setAgents(data.agents || [])
    } catch (e) {
      console.error("Failed to fetch agents", e)
    }
  }

  const fetchActivity = async () => {
    try {
      const data = await api.getSwarmActivity()
      setActivity(data.activity || [])
    } catch (e) {
      console.error("Failed to fetch activity", e)
    }
  }

  useEffect(() => {
    fetchStatus()
    fetchAgents()
    fetchActivity()
    const interval = setInterval(() => {
      fetchActivity()
      fetchStatus()
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [activity])

  const handleSubmitTask = async () => {
    if (!taskDesc) return
    setLoading(true)
    try {
      await api.submitSwarmTask({ description: taskDesc })
      setTaskDesc("")
      fetchActivity()
      fetchStatus()
    } catch (e) {
      console.error("Failed to submit task", e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[#020617] text-slate-200 swarm-grid">
      {/* Top Bar / Header */}
      <header className="h-16 border-b border-slate-800 bg-slate-950/50 backdrop-blur-md flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-4">
          <div className="h-10 w-10 bg-primary/20 rounded-xl flex items-center justify-center border border-primary/50 animate-glow">
            <Users className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Swarm War Room</h1>
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
                Multi-Agent Synthesis Online
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex -space-x-2">
            {agents.slice(0, 5).map((a, i) => (
              <div
                key={a.id}
                className="h-8 w-8 rounded-full border-2 border-slate-950 bg-slate-800 flex items-center justify-center overflow-hidden"
                title={a.name}
              >
                <Bot className="h-4 w-4" />
              </div>
            ))}
            {agents.length > 5 && (
              <div className="h-8 w-8 rounded-full border-2 border-slate-950 bg-slate-800 flex items-center justify-center text-[10px]">
                +{agents.length - 5}
              </div>
            )}
          </div>
          <div className="h-8 w-px bg-slate-800 mx-2" />
          <Button variant="outline" size="sm" className="bg-slate-900/50 border-slate-700 hover:bg-slate-800">
            <Settings2 className="h-4 w-4 mr-2" />
            Config
          </Button>
          <Badge variant="outline" className="border-primary/30 text-primary bg-primary/5 px-3 py-1 font-mono">
            {status?.pending_tasks || 0} TASKS PENDING
          </Badge>
        </div>
      </header>

      {/* Main War Room Content */}
      <div className="flex-1 flex min-h-0 overflow-hidden p-4 gap-4">

        {/* LEFT PANEL: AGENTS & STATS */}
        <div className="w-80 flex flex-col gap-4 shrink-0">
          <Card className="bg-slate-950/50 border-slate-800 backdrop-blur-sm overflow-hidden flex flex-col">
            <CardHeader className="p-4 border-b border-slate-800 bg-slate-900/30">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs uppercase tracking-wider font-bold text-slate-400 flex items-center gap-2">
                  <Cpu className="h-3 w-3" />
                  Active Synthesisers
                </CardTitle>
                <Badge variant="secondary" className="text-[9px] h-4">{agents.length}</Badge>
              </div>
            </CardHeader>
            <ScrollArea className="flex-1">
              <div className="p-3 space-y-2">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    className="p-3 rounded-lg border border-slate-800 bg-slate-900/20 hover:bg-slate-800/40 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-bold text-slate-100 group-hover:text-primary transition-colors">
                        {agent.name}
                      </span>
                      <Badge variant="outline" className="text-[9px] border-slate-700 text-slate-400">
                        {agent.model?.split('/').pop()}
                      </Badge>
                    </div>
                    <div className="text-[10px] text-slate-500 line-clamp-1 mb-2">
                      {agent.role}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-primary/60 w-3/4 animate-pulse" />
                      </div>
                      <span className="text-[9px] font-mono text-slate-600 uppercase">Idle</span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>

          <Card className="bg-slate-950/50 border-slate-800 backdrop-blur-sm shrink-0">
            <CardHeader className="p-4 border-b border-slate-800">
              <CardTitle className="text-xs uppercase tracking-wider font-bold text-slate-400 flex items-center gap-2">
                <Activity className="h-3 w-3" />
                System Telemetry
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2 rounded bg-slate-900/50 border border-slate-800/50">
                  <div className="text-[10px] text-slate-500 uppercase">Uptime</div>
                  <div className="text-sm font-mono text-slate-200">14:22:05</div>
                </div>
                <div className="p-2 rounded bg-slate-900/50 border border-slate-800/50">
                  <div className="text-[10px] text-slate-500 uppercase">Load</div>
                  <div className="text-sm font-mono text-slate-200">12.5%</div>
                </div>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] uppercase text-slate-500">
                  <span>Context Saturation</span>
                  <span>42%</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 w-[42%]" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* MIDDLE PANEL: VISUALIZATION & BUS */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          {/* Top Tabs */}
          <div className="flex items-center justify-between">
            <div className="flex bg-slate-900/50 p-1 rounded-lg border border-slate-800">
              <Button size="sm" variant="ghost" className="h-8 text-xs px-4 bg-slate-800 text-slate-100">
                <Radio className="h-3 w-3 mr-2" /> Live
              </Button>
              <Button size="sm" variant="ghost" className="h-8 text-xs px-4 text-slate-500">
                <MessageSquare className="h-3 w-3 mr-2" /> Consensus
              </Button>
              <Button size="sm" variant="ghost" className="h-8 text-xs px-4 text-slate-500">
                <Shield className="h-3 w-3 mr-2" /> Audit
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <Search className="h-4 w-4 text-slate-500" />
              <div className="h-4 w-px bg-slate-800" />
              <span className="text-[10px] font-mono text-slate-500">LOG_LEVEL: TRACE</span>
            </div>
          </div>

          {/* Activity / Message Bus */}
          <Card className="flex-1 bg-slate-950/80 border-slate-800 flex flex-col overflow-hidden backdrop-blur-xl">
            <CardHeader className="p-4 border-b border-slate-800 shrink-0 flex flex-row items-center justify-between">
              <CardTitle className="text-xs uppercase tracking-wider font-bold text-slate-400 flex items-center gap-2">
                <Terminal className="h-3 w-3 text-primary" />
                Collective Message Bus
              </CardTitle>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span className="text-[10px] text-slate-400 uppercase">L5 Analysis</span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0 flex-1 overflow-hidden relative">
              <ScrollArea className="h-full w-full" ref={scrollRef}>
                <div className="p-4 font-mono text-xs space-y-3">
                  {activity.map((msg, i) => (
                    <div key={i} className="group animate-in fade-in slide-in-from-left-2 duration-300">
                      <div className="flex items-start gap-3">
                        <div className="shrink-0 text-slate-600 mt-0.5">[{new Date().toLocaleTimeString([], { hour12: false })}]</div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className={cn(
                              "font-bold px-1 rounded",
                              msg.agent === "COORDINATOR" ? "bg-primary/20 text-primary" : "text-blue-400"
                            )}>
                              {msg.agent}
                            </span>
                            <span className="h-px w-4 bg-slate-800" />
                            <span className="text-slate-500 uppercase text-[9px] tracking-widest">{msg.type}</span>
                          </div>
                          <div className={cn(
                            "text-slate-300 leading-relaxed",
                            msg.type === "SYSTEM_EVENT" ? "text-yellow-400/80 italic" : ""
                          )}>
                            {msg.message}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {activity.length === 0 && (
                    <div className="h-full flex items-center justify-center text-slate-600 italic">
                      Waiting for swarm broadcast...
                    </div>
                  )}
                </div>
              </ScrollArea>

              {/* Overlay Gradient */}
              <div className="absolute top-0 left-0 right-0 h-8 bg-gradient-to-b from-slate-950 to-transparent pointer-events-none" />
            </CardContent>

            {/* Input Area */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/30">
              <div className="relative group">
                <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                  <ChevronRight className="h-4 w-4 text-primary group-focus-within:translate-x-1 transition-transform" />
                </div>
                <Input
                  placeholder="Inject task into message bus..."
                  className="bg-slate-950/50 border-slate-700 pl-10 h-12 text-slate-200 focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all rounded-xl"
                  value={taskDesc}
                  onChange={(e) => setTaskDesc(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSubmitTask()}
                />
                <div className="absolute inset-y-0 right-2 flex items-center">
                  <Button
                    size="sm"
                    className="h-8 px-4 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-bold shadow-lg shadow-primary/20"
                    onClick={handleSubmitTask}
                    disabled={loading}
                  >
                    {loading ? <Zap className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3 mr-2" />}
                    DISPATCH
                  </Button>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-4 px-2">
                <div className="flex items-center gap-1">
                  <div className="h-1.5 w-1.5 rounded-full bg-slate-700" />
                  <span className="text-[9px] text-slate-600 uppercase font-bold tracking-tighter">Enter to send</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-1.5 w-1.5 rounded-full bg-slate-700" />
                  <span className="text-[9px] text-slate-600 uppercase font-bold tracking-tighter">Shift+Enter for multi-line</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* RIGHT PANEL: GRAPH & TOPOLOGY */}
        <div className="w-96 flex flex-col gap-4 shrink-0">
           <Card className="flex-1 bg-slate-950/50 border-slate-800 flex flex-col overflow-hidden">
            <CardHeader className="p-4 border-b border-slate-800">
              <CardTitle className="text-xs uppercase tracking-wider font-bold text-slate-400 flex items-center gap-2">
                <Network className="h-3 w-3" />
                Topology Graph
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 flex-1 relative bg-slate-950/20">
              <VisualSwarmGraph agents={agents} />

              <div className="absolute bottom-4 left-4 right-4 bg-slate-900/80 border border-slate-800 p-2 rounded-lg backdrop-blur-md">
                <div className="text-[9px] text-slate-500 uppercase mb-1">Topology Health</div>
                <div className="flex gap-1 h-1">
                  {Array.from({ length: 20 }).map((_, i) => (
                    <div key={i} className={cn("flex-1 rounded-full", i < 15 ? "bg-primary/60" : "bg-slate-800")} />
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="h-64 bg-slate-950/50 border-slate-800 overflow-hidden">
             <CardHeader className="p-4 border-b border-slate-800">
              <CardTitle className="text-xs uppercase tracking-wider font-bold text-slate-400 flex items-center gap-2">
                <Layers className="h-3 w-3" />
                Context Layers
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              {[
                { label: "L1: Raw Source", status: "Loaded", color: "text-blue-400" },
                { label: "L2: AST Graph", status: "Indexed", color: "text-green-400" },
                { label: "L3: Call Flow", status: "Computed", color: "text-purple-400" },
                { label: "L4: Semantic Map", status: "Processing", color: "text-yellow-400" },
                { label: "L5: Executive Summary", status: "Waiting", color: "text-slate-600" },
              ].map((layer) => (
                <div key={layer.label} className="flex items-center justify-between text-[11px]">
                  <span className="font-medium text-slate-300">{layer.label}</span>
                  <span className={cn("font-mono", layer.color)}>{layer.status}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  )
}
