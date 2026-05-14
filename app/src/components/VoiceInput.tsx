import { useState, useRef, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Mic, MicOff, Loader2 } from "lucide-react"
import { useAppStore } from "@/lib/store"

let recognition: any = null

export function VoiceInput() {
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [processing, setProcessing] = useState(false)
  const { buddy, speakText, setSpeakText, processVoiceCommand } = useAppStore()

  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  const supported = !!SpeechRecognition

  const startListening = useCallback(() => {
    if (!SpeechRecognition) return
    recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = "en-US"

    recognition.onresult = (event: any) => {
      const t = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join("")
      setTranscript(t)
    }

    recognition.onend = () => {
      setListening(false)
      if (transcript) {
        setProcessing(true)
        processVoiceCommand(transcript).finally(() => setProcessing(false))
      }
    }

    recognition.onerror = () => {
      setListening(false)
    }

    recognition.start()
    setListening(true)
    setTranscript("")
  }, [SpeechRecognition, transcript, processVoiceCommand])

  const stopListening = useCallback(() => {
    if (recognition) {
      recognition.stop()
      recognition = null
    }
    setListening(false)
  }, [])

  if (!supported) return null

  return (
    <div className="relative">
      <Button
        variant={listening ? "default" : "outline"}
        size="icon"
        className={`h-9 w-9 rounded-full transition-all duration-300 ${listening ? "bg-red-500 hover:bg-red-600 animate-pulse shadow-lg shadow-red-500/50" : ""}`}
        onClick={listening ? stopListening : startListening}
        title={listening ? "Stop listening" : "Voice command"}
      >
        {processing ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : listening ? (
          <MicOff className="h-4 w-4" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </Button>
      {listening && (
        <div className="absolute top-full mt-2 right-0 bg-popover border rounded-lg p-2 shadow-lg z-50 min-w-[200px]">
          <div className="flex items-center gap-2">
            <div className="flex gap-0.5">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="w-1 bg-primary rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s`, height: `${12 + i * 4}px` }}
                />
              ))}
            </div>
            <p className="text-xs text-muted-foreground italic">Listening... {transcript && `"${transcript}"`}</p>
          </div>
        </div>
      )}
    </div>
  )
}
