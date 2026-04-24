# Telegram AI Assistant -- Agent Handover Document (2026-04)

Agent, read this document BEFORE making any changes to the project.
It describes the current architecture, stack, and conventions.

## Project Summary
Multi-modal Telegram bot: voice transcription, photo analysis, OCR, web search,
image generation, long-term memory, and scheduled reminders.

## Architecture (4 Core Modules)

| File | Role |
|---|---|
| `Scripts/tg_assistant_bot.py` | Main bot: handlers, LLM routing, agent loop, image gen cascade |
| `Scripts/agent_tools.py` | Function-calling tools (11 tools: web_search, generate_image, save_memory, etc.) |
| `Scripts/memory_manager.py` | Short-term (dict) + Long-term (SQLite + Jina embeddings) memory |
| `Scripts/leonardo_client.py` | Leonardo AI client with multi-key rotation (Nano Banana 2) |
| `Scripts/keep_alive.py` | Flask keep-alive for Render free tier |

## LLM Provider Stack (Priority Order)

| Priority | Provider | Model | Use Case |
|---|---|---|---|
| 1 | Groq (LPU) | Llama 4 Scout 17B | Primary chat, function calling |
| 2 | OpenRouter | Gemma 4 31B (paid) | Heavy OCR, complex vision |
| 3 | Groq Fallback | Llama 3.3 70B | When Scout unavailable |
| 4 | OpenRouter Free | Various free models | Ultimate fallback |

## Image Generation Cascade (Priority Order)

| Priority | Provider | Model | Cost | Notes |
|---|---|---|---|---|
| 1 | **Leonardo AI** | Nano Banana 2 | $0.04/img | 16:9 (1376x768), key rotation |
| 2 | Pollinations | zimage | Free | Authenticated |
| 3 | Pollinations | flux | Free | Authenticated |
| 4 | Pixazo | Flux-1-schnell | Free tier | Unified Gateway |
| 5 | Together AI | Flux-1-schnell | Free tier | Final fallback |

### Leonardo Key Rotation
- Keys stored in `Credentials.env` as `LEONARDO_API_KEYS: key1,key2,key3`
- `LeonardoKeyPool` rotates through keys automatically
- On HTTP 402 (insufficient funds): key marked exhausted, next key tried
- Pool status: `leonardo.get_status()` returns `{total, active, exhausted}`

## Agent Loop (Function Calling)
- Max 3 iterations per user message
- 11 tools defined in `agent_tools.py` (TOOLS list)
- JSON function calls extracted from LLM response, executed, results fed back
- Anti-loop protection: same tool+args detected -> break

## Memory System
- **Short-term:** `conversation_history[user_id]` dict, max ~50 messages
- **Long-term:** SQLite via `memory_manager.py`
  - `save_memory(user_id, content)` -- stores with Jina embedding
  - `search_memories(user_id, query)` -- semantic search
  - `create_reminder(user_id, text, time)` -- scheduled reminders
  - Background thread polls `get_due_reminders()` every 60s

## Security
- ALL keys in `Credentials.env` (gitignored)
- `<think>` blocks stripped from LLM output
- JSON leak filter: raw JSON tool calls hidden from user
- Git history was nuclear-reset (no key leaks in commits)

## Deployment
- Platform: Render (free tier)
- `keep_alive.py` runs Flask on port 10000
- Entry: `python Scripts/tg_assistant_bot.py`
- Env vars set in Render dashboard

## Key Environment Variables
```
TELEGRAM_BOT_TOKEN
GROQ_API_KEY
OPENROUTER_API_KEY
POLLINATIONS_API_KEY
PIXAZO_API_KEY
TOGETHER_API_KEY
LEONARDO_API_KEYS          # comma-separated: key1,key2,key3
SERPER_API_KEY
JINA_API_KEY
HUGGINGFACE_TOKEN
```

## How to Start
1. Read `tg_assistant_bot.py` (handlers + LLM routing + image cascade)
2. Read `Credentials.env` to understand available API keys
3. Read `GEMINI.md` for DO/WAT Framework philosophy
4. Follow Self-Improvement Loop: fix bug -> update SOP -> prevent recurrence
