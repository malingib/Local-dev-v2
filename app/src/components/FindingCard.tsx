import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  AlertCircle, AlertTriangle, Info, CheckCircle2,
  ArrowUpRight, Zap, Code
} from "lucide-react"
import type { Finding } from "@/types"
import { cn } from "@/lib/utils"

interface FindingCardProps {
  finding: Finding
  onFix: (id: string) => void
  onApprove: (id: string) => void
  onReject: (id: string) => void
}

export function FindingCard({ finding, onFix, onApprove, onReject }: FindingCardProps) {
  const severityColor = {
    critical: "text-red-500 border-red-500/20 bg-red-500/5",
    high: "text-orange-500 border-orange-500/20 bg-orange-500/5",
    medium: "text-yellow-500 border-yellow-500/20 bg-yellow-500/5",
    low: "text-blue-500 border-blue-500/20 bg-blue-500/5",
    info: "text-slate-500 border-slate-500/20 bg-slate-500/5",
  }[finding.severity] || "text-slate-500"

  const Icon = {
    critical: AlertCircle,
    high: AlertTriangle,
    medium: AlertTriangle,
    low: Info,
    info: Info,
  }[finding.severity] || Info

  return (
    <Card className="bg-slate-900/40 border-slate-800 hover:border-slate-700 transition-all group overflow-hidden">
      <div className={cn("h-1 w-full", {
        "bg-red-500": finding.severity === "critical",
        "bg-orange-500": finding.severity === "high",
        "bg-yellow-500": finding.severity === "medium",
        "bg-blue-500": finding.severity === "low",
        "bg-slate-500": finding.severity === "info",
      })} />

      <CardHeader className="p-4 pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg border", severityColor)}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className={cn("text-[10px] uppercase tracking-widest px-1.5 font-bold", severityColor)}>
                  {finding.severity}
                </Badge>
                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">{finding.type}</span>
              </div>
              <CardTitle className="text-base font-bold text-slate-100">{finding.title}</CardTitle>
            </div>
          </div>
          <Badge variant={finding.status === "open" ? "secondary" : "default"} className="text-[10px] font-mono">
            {finding.status.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-0">
        <p className="text-sm text-slate-400 mt-2 line-clamp-2">{finding.description}</p>

        <div className="mt-4 flex items-center gap-4 text-[11px] font-mono text-slate-500">
          <div className="flex items-center gap-1.5">
            <Code className="h-3 w-3" />
            <span className="truncate max-w-[200px]">
              {typeof finding.location?.file === 'string' ? finding.location.file : "Unknown Location"}
            </span>
          </div>
          {typeof finding.location?.line_start === 'number' && (
            <div className="flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full bg-slate-700" />
              <span>Line {finding.location.line_start}</span>
            </div>
          )}
        </div>

        <div className="mt-6 flex items-center justify-between pt-4 border-t border-slate-800/50">
          <div className="flex items-center gap-2">
            {finding.status === "open" && (
              <Button
                size="sm"
                className="bg-primary hover:bg-primary/90 text-primary-foreground h-8 text-xs font-bold"
                onClick={() => onFix(finding.id)}
              >
                <Zap className="h-3 w-3 mr-2 fill-current" />
                AUTOGEN FIX
              </Button>
            )}
            {finding.status === "awaiting_approval" && (
              <>
                <Button
                  size="sm"
                  className="bg-green-600 hover:bg-green-500 text-white h-8 text-xs font-bold"
                  onClick={() => onApprove(finding.id)}
                >
                  <CheckCircle2 className="h-3 w-3 mr-2" />
                  APPROVE
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-400 hover:text-red-300 hover:bg-red-400/10 h-8 text-xs font-bold"
                  onClick={() => onReject(finding.id)}
                >
                  REJECT
                </Button>
              </>
            )}
          </div>

          <Button variant="ghost" size="sm" className="h-8 text-xs text-slate-500 hover:text-slate-300 group-hover:translate-x-1 transition-transform">
            Details <ArrowUpRight className="h-3 w-3 ml-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
