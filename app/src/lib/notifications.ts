import type { Notification } from "@/types"

export interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  loading: boolean
}

export function computeUnreadCount(notifications: Notification[]): number {
  return notifications.filter((n) => !n.read).length
}

export function getNotificationIcon(type: string): string {
  const icons: Record<string, string> = {
    info: "Info",
    success: "CheckCircle",
    warning: "AlertTriangle",
    error: "XCircle",
    finding: "Bug",
    session: "Play",
    system: "Settings",
  }
  return icons[type] || "Bell"
}
