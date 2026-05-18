import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Terminal, Zap, Info, AlertTriangle, CheckCircle2, Bot, Search } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ActivityLog } from "@/types"

interface ActivityFeedProps {
  activities: ActivityLog[]
}

export function ActivityFeed({ activities }: ActivityFeedProps) {
  const getIcon = (type: string, status: string) => {
    if (status === "error") return <AlertTriangle className="h-4 w-4 text-red-500" />
    if (status === "success") return <CheckCircle2 className="h-4 w-4 text-green-500" />

    switch (type) {
      case "orchestrator": return <Zap className="h-4 w-4 text-primary" />
      case "auditor": return <Search className="h-4 w-4 text-blue-400" />
      case "agent": return <Bot className="h-4 w-4 text-purple-400" />
      default: return <Info className="h-4 w-4 text-slate-500" />
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-950/40 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
      <div className="p-4 border-b border-slate-800 bg-slate-900/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-primary" />
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-300">Live Mission Logs</h3>
        </div>
        <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-500">
          {activities.length} EVENTS
        </Badge>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {activities.length === 0 ? (
            <div className="h-32 flex flex-col items-center justify-center text-slate-600">
              <Terminal className="h-8 w-8 mb-2 opacity-20" />
              <p className="text-xs font-mono">No activity logs recorded...</p>
            </div>
          ) : (
            activities.map((activity, i) => (
              <div key={i} className="group relative pl-6 pb-4 border-l border-slate-800 last:pb-0">
                <div className={cn(
                  "absolute left-[-5px] top-0 h-2.5 w-2.5 rounded-full border-2 border-slate-950",
                  activity.status === "error" ? "bg-red-500" :
                  activity.status === "success" ? "bg-green-500" : "bg-primary"
                )} />

                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-mono text-slate-600">
                    {activity.timestamp ? new Date(activity.timestamp).toLocaleTimeString([], { hour12: false }) : "--:--:--"}
                  </span>
                  <Badge variant="outline" className="text-[9px] h-4 py-0 px-1 border-slate-800 bg-slate-900/50 text-slate-400 uppercase">
                    {activity.type}
                  </Badge>
                </div>

                <div className="flex items-start gap-3">
                  <div className="mt-0.5 opacity-50 group-hover:opacity-100 transition-opacity">
                    {getIcon(activity.type, activity.status)}
                  </div>
                  <div className="flex-1">
                    <p className={cn(
                      "text-xs leading-relaxed",
                      activity.status === "error" ? "text-red-400 font-medium" : "text-slate-300"
                    )}>
                      {activity.message}
                    </p>
                    {activity.detail && (
                      <pre className="mt-2 p-2 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-500 overflow-x-auto">
                        {activity.detail}
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            )).reverse()
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
