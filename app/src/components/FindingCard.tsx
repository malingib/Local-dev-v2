import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import type { Finding, Severity, FindingStatus } from "@/types"

const severityColors: Record<Severity, string> = {
  critical: "bg-red-500 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-yellow-500 text-white",
  low: "bg-blue-500 text-white",
  info: "bg-gray-400 text-white",
}

const statusColors: Record<FindingStatus, string> = {
  open: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  in_progress: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  awaiting_approval: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  approved: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  rejected: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
  applied: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  escalated: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
}

interface FindingCardProps {
  finding: Finding
  onFix?: (findingId: string) => void
  onApprove?: (findingId: string) => void
  onReject?: (findingId: string, reason: string) => void
}

export function FindingCard({ finding, onFix, onApprove, onReject }: FindingCardProps) {
  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge className={severityColors[finding.severity]}>
              {finding.severity}
            </Badge>
            <Badge className={statusColors[finding.status]}>
              {finding.status.replace(/_/g, " ")}
            </Badge>
          </div>
          <Badge variant="outline">{finding.type}</Badge>
        </div>
        <CardTitle className="text-lg mt-2">{finding.title}</CardTitle>
        <CardDescription className="line-clamp-2">{finding.description}</CardDescription>
      </CardHeader>
      <CardContent className="pb-2">
        {(() => {
          const loc = finding.location
          const file = loc?.file as string | undefined
          const line = loc?.line_start as number | undefined
          return file ? (
            <div className="text-sm text-muted-foreground font-mono">
              {file}
              {line && `:${line}`}
            </div>
          ) : null
        })()}
        {finding.code_snippet && (
          <>
            <Separator className="my-2" />
            <pre className="text-xs bg-muted p-3 rounded-md overflow-auto max-h-40 font-mono">
              {finding.code_snippet}
            </pre>
          </>
        )}
        {finding.suggested_fix && (
          <div className="mt-2 text-sm">
            <span className="font-medium">Suggested fix: </span>
            <span className="text-muted-foreground">{finding.suggested_fix}</span>
          </div>
        )}
      </CardContent>
      {["open", "awaiting_approval"].includes(finding.status) && (
        <CardFooter className="flex gap-2 pt-2">
          {finding.status === "open" && onFix && (
            <Button size="sm" onClick={() => onFix(finding.id)}>
              Fix
            </Button>
          )}
          {onApprove && (
            <Button size="sm" variant="default" onClick={() => onApprove(finding.id)}>
              Approve
            </Button>
          )}
          {onReject && (
            <Button size="sm" variant="outline" onClick={() => onReject(finding.id, "")}>
              Reject
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  )
}
