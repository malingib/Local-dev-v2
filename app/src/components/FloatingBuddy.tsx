import { useState, useEffect, useRef } from "react"
import { useAppStore } from "@/lib/store"
import { MessageCircle, X, Sparkles } from "lucide-react"

type Mood = "idle" | "thinking" | "happy" | "sad" | "surprised" | "working" | "success" | "error"

const MOOD_CONFIG: Record<Mood, { color: string; eye: string; mouth: string; body: string }> = {
  idle: { color: "#6366f1", eye: "👁️", mouth: "◡", body: "rounded-full" },
  thinking: { color: "#f59e0b", eye: "🤔", mouth: "○", body: "animate-pulse" },
  happy: { color: "#22c55e", eye: "😊", mouth: "▔", body: "animate-bounce" },
  sad: { color: "#6b7280", eye: "😢", mouth: "◞", body: "" },
  surprised: { color: "#3b82f6", eye: "😮", mouth: "○", body: "animate-ping" },
  working: { color: "#8b5cf6", eye: "👀", mouth: "○", body: "animate-spin-slow" },
  success: { color: "#22c55e", eye: "⭐", mouth: "▔", body: "animate-bounce" },
  error: { color: "#ef4444", eye: "😰", mouth: "◡", body: "animate-shake" },
}

export function FloatingBuddy() {
  const { buddy, buddyMood, setBuddyMood, buddyMessage, setBuddyMessage, sessionActivity } = useAppStore()
  const [visible, setVisible] = useState(true)
  const [dragging, setDragging] = useState(false)
  const [pos, setPos] = useState({ x: window.innerWidth - 180, y: 80 })
  const dragRef = useRef({ startX: 0, startY: 0, offsetX: 0, offsetY: 0 })

  useEffect(() => {
    if (!buddy) return
    const interval = setInterval(() => {
      if (buddyMood === "idle") {
        const messages = [
          "Ready to help! 🎯",
          "Say something! 🎤",
          "All systems go ✅",
          "Listening... 👂",
        ]
        setBuddyMessage(messages[Math.floor(Math.random() * messages.length)])
      }
    }, 8000)
    return () => clearInterval(interval)
  }, [buddy, buddyMood, setBuddyMessage])

  useEffect(() => {
    if (!sessionActivity) return
    setBuddyMood("working")
    setBuddyMessage(sessionActivity)
    setTimeout(() => setBuddyMood("idle"), 3000)
  }, [sessionActivity, setBuddyMood, setBuddyMessage])

  function handleMouseDown(e: React.MouseEvent) {
    setDragging(true)
    dragRef.current = { startX: e.clientX, startY: e.clientY, offsetX: pos.x, offsetY: pos.y }
  }

  useEffect(() => {
    if (!dragging) return
    function onMove(e: MouseEvent) {
      setPos({ x: dragRef.current.offsetX + (e.clientX - dragRef.current.startX), y: dragRef.current.offsetY + (e.clientY - dragRef.current.startY) })
    }
    function onUp() { setDragging(false) }
    window.addEventListener("mousemove", onMove)
    window.addEventListener("mouseup", onUp)
    return () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp) }
  }, [dragging])

  if (!buddy || !visible) return null

  const mood = MOOD_CONFIG[buddyMood] || MOOD_CONFIG.idle
  const palette = buddy.palette?.toLowerCase() || "ember"
  const bgColors: Record<string, string> = {
    ember: "from-orange-400 to-red-500", ocean: "from-blue-400 to-cyan-500",
    forest: "from-green-400 to-emerald-500", midnight: "from-indigo-600 to-purple-800",
    dawn: "from-pink-400 to-purple-500", aurora: "from-teal-400 to-blue-500",
    coral: "from-rose-400 to-pink-500", shadow: "from-gray-600 to-gray-900",
    gold: "from-yellow-400 to-amber-600", frost: "from-blue-200 to-indigo-300",
    lava: "from-red-500 to-orange-600", nebula: "from-purple-500 to-pink-600",
  }
  const bg = bgColors[palette] || "from-primary to-primary/60"
  const speciesEmoji: Record<string, string> = {
    fox: "🦊", owl: "🦉", cat: "🐱", dog: "🐶", dragon: "🐉",
    robot: "🤖", spirit: "👻", phoenix: "🦅", wolf: "🐺",
    rabbit: "🐰", bear: "🐻", squirrel: "🐿️",
  }
  const emoji = speciesEmoji[buddy.species?.toLowerCase()] || "✨"

  return (
    <div
      className="fixed z-[9999] select-none"
      style={{ left: pos.x, top: pos.y, cursor: dragging ? "grabbing" : "grab" }}
    >
      <div className="relative group">
        <button
          className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-background border shadow-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10"
          onClick={() => setVisible(false)}
        >
          <X className="h-2.5 w-2.5" />
        </button>

        <div
          className={`flex flex-col items-center gap-1 p-3 rounded-2xl bg-gradient-to-br ${bg} shadow-xl cursor-grab active:cursor-grabbing ${mood.body}`}
          onMouseDown={handleMouseDown}
        >
          <div className="text-3xl leading-none">{emoji}</div>
          <div className="flex gap-1 text-lg">{mood.eye}{mood.mouth}</div>
          {buddyMessage && (
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-popover border text-[10px] px-2 py-0.5 rounded-full whitespace-nowrap shadow-sm opacity-0 group-hover:opacity-100 transition-opacity">
              {buddyMessage}
            </div>
          )}
        </div>

        <div className="text-[9px] text-muted-foreground text-center mt-0.5 opacity-60">
          {buddy.name}
          {buddyMood !== "idle" && <Sparkles className="inline h-2.5 w-2.5 ml-1 text-yellow-500 animate-pulse" />}
        </div>
      </div>
    </div>
  )
}
