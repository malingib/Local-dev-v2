import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Bot, Send, Terminal, Users, Settings2, Activity, Network } from "lucide-react"
import * as api from "@/lib/api"
import { VisualSwarmGraph } from "@/components/VisualSwarmGraph"

export function SwarmDashboard() {
  const [status, setStatus] = useState<any>(null)
  const [agents, setAgents] = useState<any[]>([])
  const [activity, setActivity] = useState<any[]>([])
  const [taskDesc, setTaskDesc] = useState("")
  const [loading, setLoading] = useState(false)

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
    <div className="container mx-auto py-8 px-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="h-8 w-8 text-primary" />
            Agent Swarm
          </h1>
          <p className="text-muted-foreground">Collaborative multi-agent auditing system</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={status?.running ? "default" : "secondary"} className="px-3 py-1">
            {status?.running ? "Swarm Online" : "Swarm Offline"}
          </Badge>
          <Button variant="outline" size="sm" onClick={() => fetchStatus()}>
            <Activity className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
        {/* Left Column: Agents List */}
        <div className="lg:col-span-1 space-y-4 overflow-auto pr-2">
          <h2 className="text-xl font-semibold flex items-center gap-2 mb-2">
            <Bot className="h-5 w-5" />
            Active Agents
          </h2>
          {agents.map((agent) => (
            <Card key={agent.id} className="border-l-4 border-l-primary/50">
              <CardHeader className="p-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-bold">{agent.name}</CardTitle>
                  <Badge variant="outline" className="text-[10px]">
                    {agent.model}
                  </Badge>
                </div>
                <CardDescription className="text-xs line-clamp-1">{agent.role}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>

        {/* Middle/Right Column: Activity & Controls */}
        <div className="lg:col-span-3 flex flex-col gap-6 min-h-0">
          <Tabs defaultValue="activity" className="flex-1 flex flex-col min-h-0">
            <TabsList className="grid w-[600px] grid-cols-3">
              <TabsTrigger value="activity">Message Bus</TabsTrigger>
              <TabsTrigger value="graph">Interaction Graph</TabsTrigger>
              <TabsTrigger value="tasks">Tasks & Status</TabsTrigger>
            </TabsList>

            <TabsContent value="graph" className="flex-1 flex flex-col min-h-0 mt-4">
              <Card className="flex-1 flex flex-col min-h-0 border-slate-800">
                <CardHeader className="p-4 border-b border-slate-800">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Network className="h-4 w-4" />
                    Agent Interaction Graph
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0 flex-1 min-h-0">
                  <VisualSwarmGraph agents={agents} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="activity" className="flex-1 flex flex-col min-h-0 mt-4">
              <Card className="flex-1 flex flex-col min-h-0 bg-slate-950 text-slate-100 font-mono text-sm border-slate-800">
                <CardHeader className="p-4 border-b border-slate-800">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Terminal className="h-4 w-4" />
                    Live Swarm Activity
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0 flex-1 min-h-0">
                  <ScrollArea className="h-[500px] p-4">
                    <div className="space-y-2">
                      {activity.map((msg, i) => (
                        <div key={i} className="flex gap-2 animate-in fade-in slide-in-from-left-1">
                          <span className="text-primary font-bold min-w-[100px]">[{msg.agent}]</span>
                          <span className={msg.type === "SYSTEM_EVENT" ? "text-yellow-400" : ""}>
                            {msg.message}
                          </span>
                        </div>
                      ))}
                      {activity.length === 0 && (
                        <div className="text-slate-500 italic">No activity yet. Submit a task to start the swarm.</div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
                <div className="p-4 border-t border-slate-800 flex gap-2 bg-slate-900/50">
                  <Input
                    placeholder="Direct swarm task..."
                    className="bg-slate-950 border-slate-700 text-slate-100"
                    value={taskDesc}
                    onChange={(e) => setTaskDesc(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSubmitTask()}
                  />
                  <Button onClick={handleSubmitTask} disabled={loading}>
                    <Send className="h-4 w-4 mr-2" />
                    Dispatch
                  </Button>
                </div>
              </Card>
            </TabsContent>

            <TabsContent value="tasks" className="flex-1 mt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Swarm Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Running</span>
                        <span>{status?.running ? "Yes" : "No"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Active Agents</span>
                        <span>{agents.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total Tasks</span>
                        <span>{status?.total_tasks || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Pending Tasks</span>
                        <span>{status?.pending_tasks || 0}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Model Configuration</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Global Strategy</span>
                        <Badge>Expertise Weighted</Badge>
                      </div>
                      <Button variant="outline" size="sm" className="w-full">
                        <Settings2 className="h-4 w-4 mr-2" />
                        Configure Swarm
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}
