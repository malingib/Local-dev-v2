import { useLocation, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard, User, Code2, BookOpen, Sparkles, Settings,
  PanelLeftClose, PanelLeft, FlaskConical, Search, Share2,
  Brain, Palette, Server, Users, Terminal
} from "lucide-react"
import { useState } from "react"

const NAV_ITEMS = [
  { path: "/", label: "Control Center", icon: LayoutDashboard },
  { path: "/swarm", label: "War Room", icon: Users },
  { path: "/agent", label: "Soul Lab", icon: User },
  { path: "/skills", label: "Toolbox", icon: Code2 },
  { path: "/search", label: "Deep Search", icon: Search },
  { path: "/graph", label: "Project Map", icon: Share2 },
  { path: "/agent-loop", label: "Evolution", icon: Brain },
  { path: "/design", label: "Design Studio", icon: Palette },
  { path: "/specs", label: "Infra Specs", icon: Server },
  { path: "/experiments", label: "Research", icon: FlaskConical },
  { path: "/wiki", label: "Knowledge", icon: BookOpen },
  { path: "/buddy", label: "Buddy", icon: Sparkles },
  { path: "/settings", label: "Terminal Config", icon: Settings },
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
        className="fixed top-4 left-4 z-50 lg:hidden text-slate-400"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        <PanelLeft className="h-5 w-5" />
      </Button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-40 flex flex-col border-r border-slate-800 bg-slate-950 text-slate-400 transition-all duration-300",
          collapsed ? "w-20" : "w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Logo */}
        <div className={cn("flex items-center h-20 border-b border-slate-800 px-6", collapsed && "justify-center px-2")}>
          <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center shrink-0 shadow-lg shadow-primary/20">
            <Terminal className="text-primary-foreground h-6 w-6" />
          </div>
          {!collapsed && (
            <div className="ml-4 overflow-hidden">
              <span className="font-bold text-lg text-slate-100 block leading-tight">CodeAudit</span>
              <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Autonomous v2</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-6 space-y-1 px-3 overflow-y-auto">
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
                  "flex items-center w-full rounded-xl px-3 py-2.5 text-sm transition-all group relative",
                  collapsed && "justify-center px-2",
                  active
                    ? "bg-slate-900 text-primary font-bold shadow-sm"
                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-900/50"
                )}
                title={collapsed ? item.label : undefined}
              >
                {active && (
                  <div className="absolute left-0 w-1 h-6 bg-primary rounded-full" />
                )}
                <item.icon className={cn(
                  "h-5 w-5 shrink-0 transition-colors",
                  active ? "text-primary" : "group-hover:text-slate-300"
                )} />
                {!collapsed && <span className="ml-4 truncate">{item.label}</span>}
              </button>
            )
          })}
        </nav>

        {/* User / Profile Section (Static for now) */}
        {!collapsed && (
          <div className="p-4 border-t border-slate-800 mx-3 mb-2 rounded-2xl bg-slate-900/30">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
                <User className="h-4 w-4 text-slate-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-slate-200 truncate">Senior Auditor</div>
                <div className="text-[10px] text-slate-500 truncate">Lvl 42 Synthesis</div>
              </div>
            </div>
          </div>
        )}

        {/* Collapse toggle */}
        <div className="border-t border-slate-800 p-4">
          <Button
            variant="ghost"
            size="sm"
            className={cn("w-full text-slate-500 hover:text-slate-200 hover:bg-slate-900", collapsed && "justify-center")}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <PanelLeft className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5 mr-2" />}
            {!collapsed && <span className="text-xs font-bold uppercase tracking-wider">Minimize</span>}
          </Button>
        </div>
      </aside>
    </>
  )
}
