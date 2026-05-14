import { useCallback, useMemo, useRef, useEffect } from "react"
import { useAppStore } from "@/lib/store"
import { Activity, CheckCircle2, XCircle, Clock, Loader2 } from "lucide-react"

interface Node {
  id: string
  label: string
  type: "agent" | "tool" | "llm" | "finding" | "decision"
  status: "pending" | "running" | "done" | "error" | "skipped"
  duration_ms?: number
  parent_id?: string
  depth: number
}

export function AgentExecGraph() {
  const { agentExecNodes, setAgentExecNodes, currentSession } = useAppStore()
  const containerRef = useRef<HTMLDivElement>(null)
  const autoScrollRef = useRef(true)

  const statusIcon = (status: string) => {
    switch (status) {
      case "done": return <CheckCircle2 className="h-3 w-3 text-green-500 shrink-0" />
      case "error": return <XCircle className="h-3 w-3 text-red-500 shrink-0" />
      case "running": return <Loader2 className="h-3 w-3 text-blue-500 animate-spin shrink-0" />
      case "pending": return <Clock className="h-3 w-3 text-muted-foreground shrink-0" />
      default: return <Activity className="h-3 w-3 text-muted-foreground shrink-0" />
    }
  }

  const typeColor = (type: string) => {
    switch (type) {
      case "agent": return "border-l-blue-500 bg-blue-50 dark:bg-blue-950/20"
      case "tool": return "border-l-amber-500 bg-amber-50 dark:bg-amber-950/20"
      case "llm": return "border-l-purple-500 bg-purple-50 dark:bg-purple-950/20"
      case "finding": return "border-l-green-500 bg-green-50 dark:bg-green-950/20"
      case "decision": return "border-l-rose-500 bg-rose-50 dark:bg-rose-950/20"
      default: return "border-l-gray-500 bg-gray-50 dark:bg-gray-950/20"
    }
  }

  useEffect(() => {
    if (!autoScrollRef.current || !containerRef.current) return
    containerRef.current.scrollTop = containerRef.current.scrollHeight
  }, [agentExecNodes.length])

  if (agentExecNodes.length === 0 && !currentSession) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Activity className="h-8 w-8 mb-2 opacity-50" />
        <p className="text-xs">Waiting for agent activity...</p>
        <p className="text-[10px] mt-1">Start an audit or experiment to see live execution here</p>
      </div>
    )
  }

  if (agentExecNodes.length === 0 && currentSession) {
    const nodes: Node[] = [
      { id: "session", label: `Session ${currentSession.id.slice(0, 8)}`, type: "agent", status: currentSession.state === "complete" ? "done" : currentSession.state === "audit" ? "running" : "pending", depth: 0 },
      { id: "findings", label: `${currentSession.findings.length} findings`, type: "finding", status: currentSession.findings.length > 0 ? "done" : "pending", depth: 1, parent_id: "session" },
    ]
    return (
      <div ref={containerRef} className="overflow-y-auto max-h-[400px] space-y-1 p-2">
        {nodes.map((node) => (
          <div
            key={node.id}
            className={`flex items-center gap-2 text-xs p-2 rounded border-l-2 ${typeColor(node.type)}`}
            style={{ marginLeft: `${node.depth * 16}px` }}
          >
            {statusIcon(node.status)}
            <span className="font-medium">{node.label}</span>
            {node.duration_ms && <span className="text-muted-foreground ml-auto">{node.duration_ms}ms</span>}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div ref={containerRef} className="overflow-y-auto max-h-[400px] space-y-1 p-2">
      {agentExecNodes.map((node: Node) => (
        <div
          key={node.id}
          className={`flex items-center gap-2 text-xs p-2 rounded border-l-2 transition-all ${typeColor(node.type)} ${node.status === "running" ? "ring-1 ring-blue-300 dark:ring-blue-700" : ""}`}
          style={{ marginLeft: `${node.depth * 16}px` }}
        >
          {statusIcon(node.status)}
          <span className="font-medium truncate">{node.label}</span>
          {node.duration_ms && (
            <span className="text-muted-foreground ml-auto shrink-0">{node.duration_ms}ms</span>
          )}
        </div>
      ))}
    </div>
  )
}
