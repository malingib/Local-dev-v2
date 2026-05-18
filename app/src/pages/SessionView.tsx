import { useState, useEffect, useCallback } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Spinner } from "@/components/ui/spinner"
import { FindingCard } from "@/components/FindingCard"
import { ActivityFeed } from "@/components/ActivityFeed"
import { useAppStore } from "@/lib/store"
import type { Finding, FindingStatus } from "@/types"
import {
  ArrowLeft, RefreshCcw, Play, BarChart3,
  Activity as ActivityIcon, ListFilter
} from "lucide-react"
import { cn } from "@/lib/utils"

export function SessionView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const {
    currentSession,
    currentFindings,
    currentActivity,
    loading,
    selectSession,
    refreshSession,
    startAudit,
    fixFinding,
    approveFinding,
    disconnectWebSocket,
    startPolling,
  } = useAppStore()

  const [filter, setFilter] = useState<FindingStatus | "all">("all")

  useEffect(() => {
    if (id) {
      selectSession(id)
    }
    return () => {
      disconnectWebSocket()
    }
  }, [id, selectSession, disconnectWebSocket])

  // Use store-managed polling — only active when WebSocket is not available
  useEffect(() => {
    if (!currentSession) return
    const isActive =
      currentSession.state === "audit" ||
      currentSession.state === "ingest" ||
      currentSession.state === "hypothesis_loop" ||
      currentSession.state === "approval_flow"

    if (isActive) {
      startPolling()
    }
  }, [currentSession, startPolling])

  const handleStartAudit = useCallback(() => {
    if (id) startAudit(id)
  }, [id, startAudit])

  const handleFix = useCallback(
    (findingId: string) => {
      if (id) fixFinding(id, findingId)
    },
    [id, fixFinding]
  )

  const handleApprove = useCallback(
    (findingId: string) => {
      if (id) approveFinding(id, findingId, "approve")
    },
    [id, approveFinding]
  )

  const handleReject = useCallback(
    (findingId: string) => {
      if (id) approveFinding(id, findingId, "reject", "Rejected by user")
    },
    [id, approveFinding]
  )

  const filteredFindings =
    filter === "all"
      ? currentFindings
      : currentFindings.filter((f) => f.status === filter)

  const findingsByStatus = currentFindings.reduce(
    (acc, f) => {
      acc[f.status] = (acc[f.status] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  if (!id) return null

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 swarm-grid p-6">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="icon"
              onClick={() => navigate("/")}
              className="border-slate-800 bg-slate-900/50 hover:bg-slate-800 rounded-xl"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                {currentSession?.project?.name || "Audit Intelligence"}
              </h1>
              <div className="flex items-center gap-3 mt-1">
                {currentSession && (
                  <>
                    <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 uppercase text-[10px] tracking-widest font-bold">
                      {currentSession.state}
                    </Badge>
                    <div className="h-1 w-1 rounded-full bg-slate-700" />
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">{currentSession.mode}</span>
                    {currentSession.project?.path && (
                      <>
                        <div className="h-1 w-1 rounded-full bg-slate-700" />
                        <span className="font-mono text-xs text-slate-600 truncate max-w-xs">{currentSession.project.path}</span>
                      </>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => refreshSession()}
              className="border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300 rounded-xl"
            >
              <RefreshCcw className="h-4 w-4 mr-2" />
              Sync
            </Button>
            {currentSession?.state === "ingest" && (
              <Button
                onClick={handleStartAudit}
                className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold rounded-xl shadow-lg shadow-primary/20"
              >
                <Play className="h-4 w-4 mr-2 fill-current" />
                INITIATE AUDIT
              </Button>
            )}
          </div>
        </div>

        {loading && !currentSession ? (
          <div className="flex justify-center py-32">
            <Spinner className="h-8 w-8 text-primary" />
          </div>
        ) : currentSession ? (
          <Tabs defaultValue="findings" className="space-y-6">
            <div className="flex items-center justify-between">
              <TabsList className="bg-slate-900/50 border border-slate-800 p-1 rounded-xl">
                <TabsTrigger value="findings" className="rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                  <ListFilter className="h-4 w-4 mr-2" />
                  Findings ({currentFindings.length})
                </TabsTrigger>
                <TabsTrigger value="activity" className="rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                  <ActivityIcon className="h-4 w-4 mr-2" />
                  Activity
                </TabsTrigger>
                <TabsTrigger value="report" className="rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Report
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Findings Tab */}
            <TabsContent value="findings" className="space-y-6 outline-none">
              {/* Status filter buttons */}
              <div className="flex gap-2 flex-wrap p-1 bg-slate-950/50 border border-slate-800 rounded-xl w-fit">
                <Button
                  variant={filter === "all" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setFilter("all")}
                  className={cn("text-xs rounded-lg h-8", filter === "all" ? "bg-slate-800" : "text-slate-500")}
                >
                  All ({currentFindings.length})
                </Button>
                {Object.entries(findingsByStatus).map(([status, count]) => (
                  <Button
                    key={status}
                    variant={filter === status ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setFilter(status as FindingStatus)}
                    className={cn("text-xs rounded-lg h-8 uppercase", filter === status ? "bg-slate-800" : "text-slate-500")}
                  >
                    {status.replace(/_/g, " ")} ({count})
                  </Button>
                ))}
              </div>

              {/* Findings list */}
              {filteredFindings.length === 0 ? (
                <Card className="bg-slate-900/20 border-slate-800 border-dashed">
                  <CardContent className="py-24 text-center text-slate-500 font-mono text-sm">
                    NO FINDINGS MATCH THE CURRENT CRITERIA
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredFindings.map((finding: Finding) => (
                    <FindingCard
                      key={finding.id}
                      finding={finding}
                      onFix={handleFix}
                      onApprove={handleApprove}
                      onReject={handleReject}
                    />
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Activity Tab */}
            <TabsContent value="activity" className="h-[600px] outline-none">
              <ActivityFeed activities={currentActivity} />
            </TabsContent>

            {/* Report Tab */}
            <TabsContent value="report" className="space-y-6 outline-none">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Total Findings", value: currentFindings.length, color: "text-slate-200" },
                  { label: "Critical Priority", value: currentFindings.filter((f) => f.severity === "critical").length, color: "text-red-500" },
                  { label: "High Impact", value: currentFindings.filter((f) => f.severity === "high").length, color: "text-orange-500" },
                  { label: "Applied Fixes", value: currentFindings.filter((f) => f.status === "applied").length, color: "text-green-500" },
                ].map((stat) => (
                  <Card key={stat.label} className="bg-slate-900/40 border-slate-800">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-[10px] uppercase tracking-widest font-bold text-slate-500">{stat.label}</CardDescription>
                      <CardTitle className={cn("text-4xl font-black", stat.color)}>{stat.value}</CardTitle>
                    </CardHeader>
                  </Card>
                ))}
              </div>

              <Card className="bg-slate-900/40 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-sm font-bold uppercase tracking-widest text-slate-400">Security Assessment</CardTitle>
                  <CardDescription>Synthesized audit summary from multi-agent consensus</CardDescription>
                </CardHeader>
                <CardContent className="h-64 flex items-center justify-center text-slate-600 italic font-mono text-sm">
                  REACHING CONSENSUS ON FINAL REPORT...
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        ) : (
          <Card className="bg-slate-900/40 border-slate-800 border-dashed">
            <CardContent className="py-32 text-center">
              <p className="text-slate-500 font-mono text-sm mb-6">MISSION DATA NOT FOUND OR ACCESSIBLE</p>
              <Button variant="outline" className="border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-xl" onClick={() => navigate("/")}>
                RETURN TO CONTROL CENTER
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
