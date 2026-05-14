import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import type { ActivityLog } from "@/types"

const levelColors: Record<string, string> = {
  info: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  success: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  error: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
}

interface ActivityFeedProps {
  activities: ActivityLog[]
  maxItems?: number
}

export function ActivityFeed({ activities, maxItems = 50 }: ActivityFeedProps) {
  const items = activities.slice(0, maxItems)

  return (
    <ScrollArea className="h-[500px] w-full rounded-md border p-4">
      <div className="space-y-3">
        {items.length === 0 && (
          <div className="text-center text-muted-foreground text-sm py-8">
            No activity yet
          </div>
        )}
        {items.map((activity) => (
          <div key={activity.id} className="flex items-start gap-3 text-sm">
            <Badge className={levelColors[activity.level] || levelColors.info}>
              {activity.level}
            </Badge>
            <div className="flex-1 min-w-0">
              <div className="font-medium">{activity.agent}</div>
              <div className="text-muted-foreground">{activity.message}</div>
            </div>
            <div className="text-xs text-muted-foreground whitespace-nowrap">
              {new Date(activity.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}
