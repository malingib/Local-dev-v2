import { useLocation, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { LayoutDashboard, User, Code2, BookOpen, Sparkles, Settings, PanelLeftClose, PanelLeft, FlaskConical, Search, Share2, Brain, Palette, Server } from "lucide-react"
import { useState } from "react"

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/agent", label: "Agent", icon: User },
  { path: "/skills", label: "Skills", icon: Code2 },
  { path: "/search", label: "Search", icon: Search },
  { path: "/graph", label: "Graph", icon: Share2 },
  { path: "/agent-loop", label: "Agent Loop", icon: Brain },
  { path: "/design", label: "Design", icon: Palette },
  { path: "/specs", label: "Infrastructure", icon: Server },
  { path: "/experiments", label: "Research", icon: FlaskConical },
  { path: "/wiki", label: "Wiki", icon: BookOpen },
  { path: "/buddy", label: "Buddy", icon: Sparkles },
  { path: "/settings", label: "Settings", icon: Settings },
]

export function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  function isActive(path: string) {
    if (path === "/") return location.pathname === "/"
    return location.pathname.startsWith(path)
  }

  return (
    <>
      {/* Mobile hamburger */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        <PanelLeft className="h-5 w-5" />
      </Button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-40 flex flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-300",
          collapsed ? "w-16" : "w-60",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Logo */}
        <div className={cn("flex items-center h-14 border-b border-sidebar-border px-4", collapsed && "justify-center px-2")}>
          <div className="h-8 w-8 rounded-lg bg-sidebar-primary flex items-center justify-center shrink-0">
            <span className="text-sidebar-primary-foreground font-bold text-sm">CA</span>
          </div>
          {!collapsed && <span className="font-semibold text-lg ml-3">CodeAudit</span>}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.path)
            return (
              <button
                key={item.path}
                onClick={() => {
                  navigate(item.path)
                  setMobileOpen(false)
                }}
                className={cn(
                  "flex items-center w-full rounded-md px-3 py-2 text-sm transition-colors",
                  collapsed && "justify-center px-2",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                )}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span className="ml-3 truncate">{item.label}</span>}
              </button>
            )
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="border-t border-sidebar-border p-2">
          <Button
            variant="ghost"
            size="sm"
            className={cn("w-full", collapsed && "justify-center")}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4 mr-2" />}
            {!collapsed && <span className="text-xs">Collapse</span>}
          </Button>
        </div>
      </aside>
    </>
  )
}
