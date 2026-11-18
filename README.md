# CLIPFORGE AI — Autonomous Video Clipping Factory

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Platform: Windows | Linux | macOS](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](https://microsoft.com/windows)
[![Engine: FFmpeg + Faster-Whisper](https://img.shields.io/badge/Engine-FFmpeg%20%2B%20Faster--Whisper-emerald.svg)](https://ffmpeg.org)
[![UI: Glassmorphism Dark](https://img.shields.io/badge/UI-Glassmorphism%20%23080B14-8B5CF6.svg)](https://tailwindcss.com)

**CLIPFORGE AI** is an autonomous, local-first AI video clipping factory inspired by **Opus Clip**, **Klap**, and **CapCut**. It runs 100% locally on your computer through a sleek glassmorphic browser interface, transforming long-form podcasts, interviews, streams, and gaming videos into viral **9:16 vertical Shorts, TikToks, and Reels** with zero manual friction.

---

## ⚡ Key Highlights

- **100% Local-First & Private:** Runs entirely on `http://localhost:3000` (FastAPI backend on port 8000). Your videos, transcriptions, and database stay completely on your computer.
- **One-Command Setup:** Single script launches everything — checks prerequisites, installs Python & Node packages, initializes database, and opens your browser automatically.
- **Intelligent AI Editing Brain:** Formulates a complete structured JSON editing plan per clip: dynamic face & speaker tracking, smart zooms for retention, silence jump cuts, and audio loudness normalization (-14 LUFS).
- **CapCut-Style Kinetic Subtitles (36 Presets):** Dynamic word-by-word karaoke highlights with custom typography, zero jitter, and guaranteed **Bottom 22% Baseline** placement safely clear of TikTok/Shorts UI controls.
- **Clean Export Guarantee:** Captions only — zero burned-in title cards, watermarks, or topic overlays on output video files.
- **Modular AI Model Routing:** Connect **Google Gemini**, **OpenAI**, **Anthropic Claude**, **DeepSeek**, **Groq**, **Together AI**, or run **100% Free Local Ollama** (Llama 3.2, Mistral). Also includes full offline heuristic fallback.
- **Automated YouTube Studio Publishing:** Connect via Google OAuth to generate SEO titles, descriptions, hashtags, and schedule or auto-publish approved Shorts.
- **Clip Cutter (100% Free Trimmer):** Frame-accurate YouTube video and livestream segment extractor with zero API keys or service costs.

---

## ✂️ Clip Cutter (100% Free YouTube Trimmer)

Extract frame-accurate clips directly from any YouTube video, Short, or livestream without paid APIs or downloading full videos first:

- **Universal YouTube Support:** Works with standard videos, Shorts, finished live stream replays, and active livestreams with DVR.
- **Embedded Player & Interactive Range Trimmer:** Scrub directly in an embedded player, preview the selection (`Play Selection`), or click *Set to Current Player Time*.
- **Fine-Tuning Controls:** Numeric timestamp entry (`HH:MM:SS`), step nudge buttons (`±1s`, `±5s`), and quick duration buttons (`+15s`, `+30s`, `+60s`, `+90s`, `+3m`, `+5m`).
- **Flexible Quality & Audio-Only:** Download in 1080p, 720p, 480p, 360p, 240p, 144p MP4, or extract pure audio as M4A.
- **Seamless Pipeline Integration:** One-click *"Use in New Project"* button loads the cut clip straight into ClipForge's 9:16 vertical crop, caption, and viral shorts generator.
- **100% Free:** Uses only `yt-dlp` and `FFmpeg` on your machine, plus the free YouTube IFrame Player API. No API tokens or costs required.

---

## 🚀 Quick Start (One Command)

### 🪟 Windows (Recommended)
Simply double-click **`START.bat`** (or run it in Command Prompt / PowerShell):
```cmd
START.bat
```
*`START.bat` automatically verifies Python 3.10+, Node.js, and FFmpeg, configures `.env`, installs dependencies, initializes the SQLite database with all 36 presets, and boots the application in your browser.*

### 🐧 Linux & 🍎 macOS
Make the script executable and run:
```bash
chmod +x start.sh
./start.sh
```

---

## 📦 Prerequisites

1. **Python 3.10+** (ensure *"Add Python to PATH"* is checked on Windows)
2. **Node.js 18+** & npm
3. **FFmpeg** installed and accessible via system `PATH`
   - Windows: Download from [Gyan.dev FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/)
   - Ubuntu/Debian: `sudo apt update && sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

---

## ⚙️ Configuration & Secrets (.env)

ClipForge AI runs out-of-the-box in local offline mode without any paid API keys. To enable cloud LLMs (Gemini, OpenAI, Groq) or YouTube publishing, copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Key | Description | Default |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API (Flash 2.5 / Pro) | *(Optional)* |
| `OPENAI_API_KEY` | OpenAI API (GPT-4o, o3-mini) | *(Optional)* |
| `GROQ_API_KEY` | Groq high-speed LPU inference | *(Optional)* |
| `OLLAMA_BASE_URL` | Local free Ollama instance | `http://localhost:11434` |
| `HARDWARE_PROFILE` | Performance mode (`ECO`, `BALANCED`, `QUALITY`) | `BALANCED` |
| `DEFAULT_WHISPER_MODEL` | Speech-to-text accuracy (`tiny`, `base`, `small`, `medium`) | `base` |

> 🔒 **Security Notice:** `.env`, `.db` files, and all media in `storage/` are strictly excluded in `.gitignore` to guarantee your personal data and keys are never published or exposed.

---

## 🎬 36 Signature Caption Presets

ClipForge AI includes 36 customizable subtitle animation styles:

1. **MrBeast Bold:** High-impact bold yellow/white text with punchy dynamic pop.
2. **Hormozi Emphasis:** Electric emerald green keyword highlights with fast cadence.
3. **Neon Glow & Neon Gaming:** Electric cyan and hot-magenta neon drop-shadow glow.
4. **Boxed & Boxed Subtitles:** Rounded dark contrast badges behind active phrases.
5. **Highlighter & Marker Sweep:** Authentic highlighter pen strip behind active words.
6. **Fire & Lava:** Warm orange/crimson gradient with dynamic fiery aura.
7. **Comic Pop:** 3D comic edge drop-shadows with vibrant yellow font.
8. **Clean White Subtitles:** Pristine modern white typography with soft drop-shadow.
9. **RGB Chroma Gaming:** Multi-color shifting border with gaming energy.
10. **Cinematic Subtitles:** Warm theater yellow with lower-third placement.
11. **Karaoke Word Highlighting:** Real-time vocal tracker with active word fill.
12. ...plus **25 more viral presets** tailored for podcasts, gaming, reactions, and tutorials!

---

## 🏗️ Architecture

```
clipforge-ai/
├── backend/                   # FastAPI + SQLite + Faster-Whisper + FFmpeg Engine
│   ├── ai/                    # Transcription, Viral Analyzer, Editing Brain, Reviewer
│   ├── api/                   # REST API routers (projects, clips, clipcutter, automation, captions)
│   ├── captions/              # ASS subtitle generator with karaoke word tags
│   ├── core/                  # Database manager, security vault, hardware tuner
│   ├── providers/             # Gemini, OpenAI, Claude, Groq, Ollama adapters
│   ├── video/                 # FFmpeg filter graphs, face tracker, silence remover
│   └── workers/               # 9-stage autonomous pipeline worker
├── frontend/                  # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/        # CaptionStylePicker, GlassCard, Metrics, Sidebar
│   │   ├── screens/           # Dashboard, NewProject, Processing, Gallery, Analytics
│   │   └── services/          # REST client & WebSocket streaming
├── config/                    # Default configurations & preset registries
├── storage/                   # Local uploads, clips, previews, and SQLite DB (gitignored)
├── START.bat                  # One-command Windows launcher
├── start.sh                   # One-command Linux/macOS launcher
├── STOP.bat                   # Clean shutdown utility
├── .env.example               # Safe environment template
├── requirements.txt           # Python dependencies
└── package.json               # Frontend dependencies & scripts
```

---

## 📄 License
MIT License. Open-source, local-first, autonomous video creation.
