"""
Voice interface module — inspired by microsoft/VibeVoice (47k★).
Provides TTS and ASR capabilities for the Buddy companion system.
Supports pluggable backends: local pyttsx3, VibeVoice API, or streaming.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime


BACKENDS = {
    "pyttsx3": "local offline TTS (basic quality, no dependencies beyond Python stdlib)",
    "vibevoice": "Microsoft VibeVoice API — frontier TTS with 7.5Hz tokenizers",
    "elevenlabs": "ElevenLabs API — high-quality cloud TTS",
    "none": "disabled — no voice output",
}

VOICES = {
    "default": {"gender": "neutral", "description": "Default system voice"},
    "buddy_friendly": {"gender": "warm", "description": "Friendly companion voice for Buddy"},
    "buddy_wise": {"gender": "calm", "description": "Wise, calm voice for mentor mode"},
    "announce": {"gender": "clear", "description": "Clear announcement voice for notifications"},
}


def get_available_backends() -> list:
    available = ["none"]
    try:
        import pyttsx3
        available.append("pyttsx3")
    except ImportError:
        pass
    available.append("vibevoice")
    available.append("elevenlabs")
    return available


def speak(text: str, voice: str = "default", backend: str = "auto") -> dict:
    if backend == "auto":
        backend = _detect_best_backend()
    if backend == "none" or not backend:
        return {"spoken": False, "reason": "Voice disabled", "text": text}

    text = text.strip()
    if not text:
        return {"spoken": False, "reason": "Empty text"}

    try:
        if backend == "pyttsx3":
            return _speak_pyttsx3(text, voice)
        elif backend == "vibevoice":
            return _speak_vibevoice(text, voice)
        elif backend == "elevenlabs":
            return _speak_elevenlabs(text, voice)
        else:
            return {"spoken": False, "reason": f"Unknown backend: {backend}"}
    except Exception as e:
        return {"spoken": False, "error": str(e), "text": text}


def _detect_best_backend() -> str:
    try:
        import pyttsx3
        return "pyttsx3"
    except ImportError:
        pass
    if os.environ.get("VIBEVOICE_API_KEY"):
        return "vibevoice"
    if os.environ.get("ELEVENLABS_API_KEY"):
        return "elevenlabs"
    return "none"


def _speak_pyttsx3(text: str, voice: str = "default") -> dict:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 180)
    engine.setProperty("volume", 0.9)
    engine.say(text)
    engine.runAndWait()
    engine.stop()
    return {"spoken": True, "backend": "pyttsx3", "text": text, "voice": voice}


def _speak_vibevoice(text: str, voice: str = "default") -> dict:
    api_key = os.environ.get("VIBEVOICE_API_KEY", "")
    if not api_key:
        return {"spoken": False, "reason": "VIBEVOICE_API_KEY not set"}

    import requests
    resp = requests.post(
        "https://api.vibevoice.ai/v1/tts",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"text": text, "voice": voice, "format": "wav"},
        timeout=30,
    )
    if resp.status_code == 200:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(resp.content)
            wav_path = f.name
        try:
            import subprocess
            subprocess.run(["aplay", wav_path], capture_output=True, timeout=30)
        except Exception:
            pass
        finally:
            Path(wav_path).unlink(missing_ok=True)
        return {"spoken": True, "backend": "vibevoice", "text": text, "voice": voice}
    return {"spoken": False, "reason": f"VibeVoice API error: {resp.status_code}"}


def _speak_elevenlabs(text: str, voice: str = "default") -> dict:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        return {"spoken": False, "reason": "ELEVENLABS_API_KEY not set"}

    voice_map = {"default": "21m00Tcm4TlvDq8ikWAM", "buddy_friendly": "21m00Tcm4TlvDq8ikWAM",
                 "buddy_wise": "pNInz6obpgDQGcFmaJgB", "announce": "ODq5zmih8GrVee37X1oX"}
    voice_id = voice_map.get(voice, voice_map["default"])

    import requests
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={"text": text, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
        timeout=30,
    )
    if resp.status_code == 200:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(resp.content)
            mp3_path = f.name
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", mp3_path], capture_output=True, timeout=30)
        except Exception:
            pass
        finally:
            Path(mp3_path).unlink(missing_ok=True)
        return {"spoken": True, "backend": "elevenlabs", "text": text, "voice": voice}
    return {"spoken": False, "reason": f"ElevenLabs API error: {resp.status_code}"}


def transcribe(audio_path: str, backend: str = "auto") -> dict:
    if backend == "auto":
        backend = "vibevoice" if os.environ.get("VIBEVOICE_API_KEY") else "none"

    if backend == "none":
        return {"transcribed": False, "reason": "No ASR backend available"}

    if not Path(audio_path).exists():
        return {"transcribed": False, "reason": "Audio file not found"}

    try:
        if backend == "vibevoice":
            api_key = os.environ.get("VIBEVOICE_API_KEY", "")
            if not api_key:
                return {"transcribed": False, "reason": "VIBEVOICE_API_KEY not set"}
            import requests
            with open(audio_path, "rb") as f:
                resp = requests.post(
                    "https://api.vibevoice.ai/v1/asr",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": f},
                    timeout=30,
                )
            if resp.status_code == 200:
                return {"transcribed": True, "text": resp.json().get("text", ""), "backend": "vibevoice"}
            return {"transcribed": False, "reason": f"ASR error: {resp.status_code}"}
    except Exception as e:
        return {"transcribed": False, "error": str(e)}

    return {"transcribed": False, "reason": "ASR failed"}


def get_voice_status() -> dict:
    return {
        "available_backends": get_available_backends(),
        "detected_backend": _detect_best_backend(),
        "voices": list(VOICES.keys()),
        "has_vibevoice_key": bool(os.environ.get("VIBEVOICE_API_KEY")),
        "has_elevenlabs_key": bool(os.environ.get("ELEVENLABS_API_KEY")),
    }
