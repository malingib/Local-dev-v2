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
  }, [id])

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
  }, [currentSession?.state])

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
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-6 px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={() => navigate("/")}>
                ← Back
              </Button>
              <h1 className="text-2xl font-bold">
                {currentSession?.project?.name || "Loading..."}
              </h1>
            </div>
            {currentSession && (
              <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                <Badge variant="outline">{currentSession.state}</Badge>
                <Badge variant="outline">{currentSession.mode}</Badge>
                {currentSession.project?.path && (
                  <span className="font-mono text-xs">{currentSession.project.path}</span>
                )}
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refreshSession()}>
              Refresh
            </Button>
            {currentSession?.state === "ingest" && (
              <Button onClick={handleStartAudit}>
                Start Audit
              </Button>
            )}
          </div>
        </div>

        {loading && !currentSession ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : currentSession ? (
          <Tabs defaultValue="findings">
            <TabsList className="mb-4">
              <TabsTrigger value="findings">
                Findings ({currentFindings.length})
              </TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
              <TabsTrigger value="report">Report</TabsTrigger>
            </TabsList>

            {/* Findings Tab */}
            <TabsContent value="findings" className="space-y-4">
              {/* Status filter buttons */}
              <div className="flex gap-2 flex-wrap">
                <Button
                  variant={filter === "all" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFilter("all")}
                >
                  All ({currentFindings.length})
                </Button>
                {Object.entries(findingsByStatus).map(([status, count]) => (
                  <Button
                    key={status}
                    variant={filter === status ? "default" : "outline"}
                    size="sm"
                    onClick={() => setFilter(status as FindingStatus)}
                  >
                    {status.replace(/_/g, " ")} ({count})
                  </Button>
                ))}
              </div>

              {/* Findings list */}
              {filteredFindings.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    No findings match this filter
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
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
            <TabsContent value="activity">
              <ActivityFeed activities={currentActivity} />
            </TabsContent>

            {/* Report Tab */}
            <TabsContent value="report">
              <Card>
                <CardHeader>
                  <CardTitle>Audit Report</CardTitle>
                  <CardDescription>Summary of findings</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-3xl">{currentFindings.length}</CardTitle>
                        <CardDescription>Total Findings</CardDescription>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-3xl text-red-500">
                          {currentFindings.filter((f) => f.severity === "critical").length}
                        </CardTitle>
                        <CardDescription>Critical</CardDescription>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-3xl text-orange-500">
                          {currentFindings.filter((f) => f.severity === "high").length}
                        </CardTitle>
                        <CardDescription>High</CardDescription>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-3xl text-green-500">
                          {currentFindings.filter((f) => f.status === "applied").length}
                        </CardTitle>
                        <CardDescription>Applied</CardDescription>
                      </CardHeader>
                    </Card>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">Session not found</p>
              <Button variant="link" onClick={() => navigate("/")}>
                Go back to dashboard
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
