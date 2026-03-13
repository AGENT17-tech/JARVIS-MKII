# J.A.R.V.I.S — MKII v2.0

> *Just A Rather Very Intelligent System*
> Built by **Khalid Walid** — polymath engineer, successor of Tony Stark.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Status](https://img.shields.io/badge/status-operational-brightgreen)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2024.04-orange)
![Model](https://img.shields.io/badge/LLM-qwen3%3A1.7b%20%7C%20Ollama-purple)

---

## Overview

JARVIS MKII is a fully local, voice-enabled AI desktop assistant running on Ubuntu 24.04. It features a cinematic Electron/React HUD, a FastAPI orchestrator backend, local LLM inference via Ollama, persistent memory, wake word detection, Whisper STT, Kokoro TTS, and moondream screen vision — all running offline with no cloud dependency.

---

## Repository Structure

```
JARVIS-MKII/
├── core/                  # Python FastAPI backend
│   ├── main.py            # Orchestrator — routes, streaming, voice pipeline
│   ├── memory.py          # SQLite memory — entities, history, context
│   ├── voice.py           # Whisper STT + Kokoro TTS + wake word
│   ├── vision.py          # moondream screen/image analysis
│   ├── actions.py         # Tool definitions + execution
│   └── wakeword/          # Wake word model (hey_jarvis)
│
├── hud/                   # Electron + React frontend
│   ├── src/               # React components + HUD panels
│   ├── electron/          # Electron main process
│   ├── public/            # Static assets
│   └── vite.config.js     # Vite build config
│
└── README.md
```

---

## System Architecture

```
┌─────────────────────────────┐
│      HUD (Electron/React)   │
│  Weather · GitHub · Chat    │
└────────────┬────────────────┘
             │ HTTP + WebSocket
             ▼
┌─────────────────────────────┐
│   FastAPI Orchestrator      │
│   uvicorn · port 8000       │
│   systemd: jarvis-core      │
└──┬──────────┬───────────────┘
   │          │          │
   ▼          ▼          ▼
Ollama     SQLite     Voice Pipeline
qwen3:1.7b  Memory    Whisper + Kokoro
moondream   Entities  Wake word
```

---

## Hardware

| Component | Spec |
|-----------|------|
| Machine | HP ZBook 15 G6 |
| OS | Ubuntu 24.04 LTS |
| GPU | NVIDIA T1000 (4GB VRAM) |
| LLM | qwen3:1.7b (fits entirely in VRAM) |
| STT | Whisper (local) |
| TTS | Kokoro-82M (CUDA) |
| Vision | moondream:latest (Ollama) |

---

## Prerequisites

### System
- Ubuntu 24.04 LTS
- Python 3.12
- Node.js 18+
- NVIDIA GPU with CUDA (recommended)

### Services
- [Ollama](https://ollama.com) installed and running
- Required models pulled:

```bash
ollama pull qwen3:1.7b
ollama pull moondream
```

### Python dependencies

```bash
pip install fastapi uvicorn httpx python-dotenv pydantic \
            openai-whisper torch torchaudio \
            kokoro sounddevice soundfile \
            mss pillow aiosqlite --break-system-packages
```

### Node dependencies

```bash
cd hud
npm install
```

---

## Configuration

Create `core/.env`:

```env
GEMINI_API_KEY=your_key_here        # Optional — only needed if switching to Gemini
GEMINI_MODEL=gemini-2.0-flash       # Optional
HF_HUB_OFFLINE=1                    # Run fully offline
HF_HUB_DISABLE_PROGRESS_BARS=1
```

---

## Running JARVIS

### Backend (via systemd)

```bash
# Start
sudo systemctl start jarvis-core

# Stop
sudo systemctl stop jarvis-core

# Status + logs
systemctl status jarvis-core
journalctl -u jarvis-core -f
```

### Backend (manual)

```bash
cd core
uvicorn main:app --host 0.0.0.0 --port 8000
```

### HUD (development)

```bash
cd hud
npm run dev
```

### HUD (production build)

```bash
cd hud
npm run build
npm run electron
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System status + memory stats |
| GET | `/greeting` | Time-aware greeting with live weather |
| GET | `/weather` | Live Cairo weather (Open-Meteo) |
| POST | `/chat` | Streaming LLM response |
| POST | `/speak` | TTS speak request |
| GET | `/github` | AGENT17-tech repos + commit activity |
| WS | `/ws` | WebSocket for voice/speaking events |
| POST | `/vision/screen` | Capture + analyse screen |
| POST | `/vision/image` | Analyse image file |
| GET | `/vision/context` | One-sentence screen summary |
| DELETE | `/memory` | Clear conversation history |
| GET | `/memory/stats` | Memory database statistics |
| GET | `/memory/entities` | Persistent user facts |
| POST | `/memory/entity` | Set a persistent user fact |
| POST | `/shutdown` | Farewell + power down |

---

## systemd Service

Located at `/etc/systemd/system/jarvis-core.service`:

```ini
[Unit]
Description=JARVIS Core — FastAPI Backend
After=network.target

[Service]
Type=simple
User=kiko
WorkingDirectory=/home/kiko/JARVIS-MKII/core
ExecStart=/home/kiko/.local/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
Environment=PATH=/home/kiko/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=HOME=/home/kiko
Environment=HF_HUB_OFFLINE=1
Environment=HF_HUB_DISABLE_PROGRESS_BARS=1

[Install]
WantedBy=multi-user.target
```

---

## Voice Pipeline

1. Microphone input → **openWakeWord** detects `hey_jarvis`
2. Audio recorded → **Whisper** transcribes to text
3. Text → **FastAPI** `/chat` → **Ollama** streams response
4. Response → sentence splitter → **Kokoro TTS** → audio output
5. WebSocket broadcasts `speaking:start` / `speaking:stop` to HUD

---

## Memory System

JARVIS uses a three-tier SQLite memory architecture:

- **Entities** — persistent facts about the user (name, preferences). Never cleared.
- **Summaries** — compressed long-term conversation history.
- **Raw exchanges** — recent uncompressed turns for sharp short-term recall.

Clear conversation history (entities preserved):
```bash
curl -X DELETE http://localhost:8000/memory
```

---

## Changelog

### v2.0 — MKII (2026-03-13)
- Migrated LLM backend to local Ollama (`qwen3:1.7b`) — no cloud dependency
- Fixed `GEMINI_STREAM_URL` NameError crashing `/chat` endpoint
- Stream-level token sanitization (caps normalization)
- SQLite memory confirmed operational with entity persistence
- Whisper STT + Kokoro TTS + moondream vision all active under systemd
- Identity configured: created by Khalid Walid, successor of Tony Stark

### v1.x — Initial build
- FastAPI orchestrator + Electron HUD wired together
- Basic chat, weather, GitHub panel operational
- Voice pipeline scaffolded

---

## Creator

**Khalid Walid** — AGENT17-tech
Polymath engineer. Tony Stark's successor.
GitHub: [AGENT17-tech](https://github.com/AGENT17-tech)

---

*"Sometimes you gotta run before you can walk." — Tony Stark*
