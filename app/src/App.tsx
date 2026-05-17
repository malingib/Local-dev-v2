import { useEffect } from "react"
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom"
import { Dashboard } from "@/pages/Dashboard"
import { SwarmDashboard } from "@/pages/SwarmDashboard"
import { SessionView } from "@/pages/SessionView"
import { Settings } from "@/pages/Settings"
import { Agent } from "@/pages/Agent"
import { SkillsPage } from "@/pages/SkillsPage"
import { SearchPage } from "@/pages/SearchPage"
import { GraphPage } from "@/pages/GraphPage"
import { AgentLoopPage } from "@/pages/AgentLoopPage"
import { DesignPage } from "@/pages/DesignPage"
import { SpecsPage } from "@/pages/SpecsPage"
import { WikiPage } from "@/pages/WikiPage"
import { BuddyPage } from "@/pages/BuddyPage"
import { Toaster } from "@/components/ui/sonner"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import { Sidebar } from "@/components/Sidebar"
import { FloatingBuddy } from "@/components/FloatingBuddy"
import { VoiceInput } from "@/components/VoiceInput"

function ElectronRouter() {
  const navigate = useNavigate()
  useEffect(() => {
    const handler = (e: CustomEvent) => {
      const route = e.detail
      if (typeof route === "string") {
        navigate(route)
      }
    }
    window.addEventListener("electron:navigate", handler as EventListener)
    return () => window.removeEventListener("electron:navigate", handler as EventListener)
  }, [navigate])
  return null
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ElectronRouter />
        <div className="flex h-screen">
          <Sidebar />
          <main className="flex-1 overflow-auto relative">
            <div className="fixed bottom-4 right-4 z-50">
              <VoiceInput />
            </div>
            <FloatingBuddy />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/swarm" element={<SwarmDashboard />} />
              <Route path="/session/:id" element={<SessionView />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/agent" element={<Agent />} />
              <Route path="/skills" element={<SkillsPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/graph" element={<GraphPage />} />
              <Route path="/agent-loop" element={<AgentLoopPage />} />
              <Route path="/design" element={<DesignPage />} />
              <Route path="/specs" element={<SpecsPage />} />
              <Route path="/wiki" element={<WikiPage />} />
              <Route path="/buddy" element={<BuddyPage />} />
            </Routes>
          </main>
        </div>
        <Toaster />
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
