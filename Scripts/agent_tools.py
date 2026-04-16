"""
agent_tools.py — Инструменты для Agent Loop (Function Calling).

Каждый инструмент состоит из:
1. JSON-схемы (для передачи LLM, чтобы она знала, что можно вызвать).
2. Исполнителя (Python-функция, которая реально выполняет действие).

LLM видит ТОЛЬКО схемы. Когда она решает вызвать инструмент,
Agent Loop запускает соответствующий исполнитель и отдает результат обратно LLM.
"""

import os
import json
import random
import time
import re
import requests as http_requests
from memory_manager import (
    save_memory, search_memories, jina_search, jina_read_url,
    get_all_memories, clear_user_memories,
    create_reminder, get_user_reminders, cancel_reminder as db_cancel_reminder
)

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

DEFAULT_REGION = "Беларусь"

# ============================================================
# TOOL DEFINITIONS (JSON schemas for LLM)
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the internet for fresh, up-to-date information. "
                "Use when you need current news, prices, weather forecasts, facts, "
                "product reviews, people info, or anything you're not sure about. "
                "Always prefer searching over guessing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in the language most appropriate for the topic. For Belarus/Russia topics, use Russian."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": (
                "Read and extract the full text of a specific webpage URL. "
                "Use when you need deeper information from a specific link, "
                "or when search snippets are not enough to answer the question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL of the webpage to read."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": (
                "Generate an image based on a text description. "
                "Use when the user asks to draw, create, generate, or visualize something. "
                "Also use when they say 'нарисуй', 'изобрази', 'сгенерируй картинку'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Detailed image description in the user's original language."
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get weather forecast for a specific city. "
                "Use when the user asks about weather, temperature, rain, wind, etc. "
                "Supports forecasts from 1 to 7 days ahead. "
                "If user asks about tomorrow, set forecast_days=2. "
                "If user asks about weather for the next 3 days, set forecast_days=3. "
                "Default to Belarus if no country is specified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., 'Минск', 'Москва', 'London')."
                    },
                    "country_hint": {
                        "type": "string",
                        "description": "Optional country name for disambiguation (e.g., 'Беларусь', 'Россия')."
                    },
                    "forecast_days": {
                        "type": "integer",
                        "description": "Number of days to forecast (1=today only, 2=today+tomorrow, up to 7). Default: 1."
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": (
                "Save an important fact about the user to long-term memory. "
                "Use when the user shares personal preferences, important info, "
                "or explicitly asks to remember something. "
                "Examples: 'Запомни, я люблю кофе', 'Мой день рождения 5 мая', 'У меня аллергия на орехи'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "The fact to remember, written clearly and concisely in Russian."
                    }
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memories",
            "description": (
                "Search long-term memory for previously saved facts about the user. "
                "Use when you need to recall user preferences, past conversations, or stored info. "
                "Also use proactively when you think context from memory would improve a response."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in memory (e.g., 'аллергии', 'любимая еда', 'день рождения')."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draw_tarot_card",
            "description": (
                "Draw a random Tarot card and generate its mystical interpretation with an image. "
                "YOU MUST ALWAYS call this tool when the user asks for tarot, fortune telling, "
                "card reading, or says 'погадай', 'погадай мне', 'вытяни карту', 'расклад'. "
                "NEVER try to do a tarot reading yourself — ALWAYS use this tool. "
                "The tool will generate a card image and return the card info for your interpretation."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_horoscope",
            "description": (
                "Generate a daily horoscope for a specific zodiac sign. "
                "Use when the user asks about their horoscope or zodiac prediction."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sign": {
                        "type": "string",
                        "description": "Zodiac sign in Russian (e.g., 'Овен', 'Телец', 'Близнецы').",
                        "enum": ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", 
                                 "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
                    }
                },
                "required": ["sign"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": (
                "Set a personal reminder for the user. The reminder will be sent as a Telegram message at the specified time. "
                "Use when the user says things like 'напомни', 'remind me', 'через 30 минут', 'завтра в 9'. "
                "You MUST calculate the exact Unix timestamp for remind_at based on the user's request and the current time. "
                "Current timezone: Europe/Minsk (UTC+3)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "What to remind the user about (in Russian)."
                    },
                    "remind_at": {
                        "type": "number",
                        "description": "Unix timestamp (seconds since epoch) for when to send the reminder. Calculate this from the current time + requested delay."
                    },
                    "human_time": {
                        "type": "string",
                        "description": "Human-readable time description for confirmation, e.g. 'через 30 минут', 'завтра в 9:00'."
                    }
                },
                "required": ["text", "remind_at", "human_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_reminders",
            "description": (
                "List all active (pending) reminders for the user. "
                "Use when the user asks 'мои напоминания', 'какие напоминания', 'что запланировано'."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_reminder",
            "description": (
                "Cancel a pending reminder by its ID. "
                "Use when the user wants to cancel or delete a reminder. "
                "First call list_reminders to show available reminders and their IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "The ID of the reminder to cancel."
                    }
                },
                "required": ["reminder_id"]
            }
        }
    }
]


# ============================================================
# TOOL EXECUTORS (actual Python functions that do the work)
# ============================================================

def execute_tool(tool_name: str, arguments: dict, context: dict = None) -> str:
    """
    Execute a tool by name with given arguments.
    Returns a string result that will be sent back to LLM.
    
    context dict can contain: user_id, bot, message, etc.
    """
    context = context or {}
    
    executors = {
        "search_web": _exec_search_web,
        "read_webpage": _exec_read_webpage,
        "generate_image": _exec_generate_image,
        "get_weather": _exec_get_weather,
        "remember_fact": _exec_remember_fact,
        "recall_memories": _exec_recall_memories,
        "draw_tarot_card": _exec_draw_tarot,
        "get_horoscope": _exec_get_horoscope,
        "set_reminder": _exec_set_reminder,
        "list_reminders": _exec_list_reminders,
        "cancel_reminder": _exec_cancel_reminder,
    }
    
    executor = executors.get(tool_name)
    if not executor:
        return f"Error: Unknown tool '{tool_name}'"
    
    try:
        return executor(arguments, context)
    except Exception as e:
        return f"Error executing {tool_name}: {e}"


# --- Individual Executors ---

def localize_search_query(query):
    """Добавляет регион к запросу, если тема касается локальных новостей/цен."""
    q_lower = query.lower()
    regional_topics = [
        "погода", "новости", "курс", "цена", "купить", "билет", 
        "кино", "афиша", "закон", "налог", "ваканси",
        "зарплат", "пенси", "пособи",
    ]
    if any(topic in q_lower for topic in regional_topics):
        if "беларусь" not in q_lower and "рб" not in q_lower and "минск" not in q_lower:
            return f"{query} {DEFAULT_REGION}"
    return query

def _search_ddgs(search_query):
    """Попытка поиска через библиотеку ddgs."""
    if not DDGS_AVAILABLE:
        return []
    try:
        results = list(DDGS().text(search_query, max_results=3))
        return [{"title": r.get("title", ""), "body": r.get("body", "")} for r in results]
    except Exception as e:
        print(f"⚠️ DDGS library failed: {e}")
        return []

def _search_html_fallback(search_query):
    """Фоллбэк: прямой запрос к HTML-версии DuckDuckGo."""
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": "https://duckduckgo.com/"
        }
        resp = http_requests.post(url, data={"q": search_query}, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
        
        results = []
        snippets = re.findall(
            r'class="result__a"[^>]*>([^<]+)</a>.*?class="result__snippet"[^>]*>(.*?)</span>',
            resp.text, re.DOTALL
        )
        for title, body in snippets[:3]:
            clean_body = re.sub(r'<[^>]+>', '', body).strip()
            results.append({"title": title.strip(), "body": clean_body})
        return results
    except Exception as e:
        print(f"⚠️ DDG HTML fallback failed: {e}")
        return []

def _search_serper(search_query):
    """Поиск через Serper.dev API (Google)."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return []
    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = json.dumps({"q": search_query, "gl": "by", "hl": "ru", "num": 3})
        resp = http_requests.post(url, headers=headers, data=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = []
            answer = data.get("answerBox", {})
            if answer and "answer" in answer:
                results.append({"title": "Прямой ответ", "body": answer["answer"]})
            elif answer and "snippet" in answer:
                results.append({"title": "Краткий ответ", "body": answer["snippet"]})
            
            kg = data.get("knowledgeGraph", {})
            if kg and "description" in kg:
                results.append({"title": kg.get("title", "Факт"), "body": kg["description"]})

            for r in data.get("organic", [])[:3]:
                if len(results) >= 4: break
                results.append({"title": r.get("title", ""), "body": r.get("snippet", "")})
            return results
        return []
    except Exception as e:
        print(f"⚠️ Serper search failed: {e}")
        return []

def perform_web_search(query):
    """Единая точка входа для поиска с каскадными фоллбэками и маркерами."""
    search_query = localize_search_query(query)
    print(f"🔍 Унифицированный поиск: {search_query}")
    
    # Каскад: Serper -> DDGS -> HTML
    results = _search_serper(search_query)
    if not results:
        results = _search_ddgs(search_query)
    if not results:
        results = _search_html_fallback(search_query)
    
    if not results:
        # Последний шанс: Jina (если она еще работает в этом окружении)
        jina_res = jina_search(search_query, max_results=3)
        if jina_res:
            return f"\n=== SEARCH DATA START ===\n{jina_res}\n=== SEARCH DATA END ===\n"
        return "Поиск не дал результатов."
    
    context = "\n=== SEARCH DATA START ===\n"
    context += f"🔍 Результаты веб-поиска для запроса: {search_query}\n"
    for i, r in enumerate(results, 1):
        context += f"{i}. {r['title']}: {r['body']}\n"
    context += "=== SEARCH DATA END ===\n"
    return context

def _exec_search_web(args: dict, ctx: dict) -> str:
    """Инструмент Agent Loop: Использование унифицированного поиска."""
    query = args.get("query", "")
    if not query:
        return "Error: empty search query"
    return perform_web_search(query)


def _exec_read_webpage(args: dict, ctx: dict) -> str:
    """Read a specific webpage via Jina Reader."""
    url = args.get("url", "")
    if not url:
        return "Error: empty URL"
    content = jina_read_url(url)
    return content if content else "Не удалось прочитать страницу."


def _exec_generate_image(args: dict, ctx: dict) -> str:
    """
    Signal to the Agent Loop that an image needs to be generated.
    The actual generation happens in the main bot code.
    Returns a special marker that the Agent Loop intercepts.
    """
    prompt = args.get("prompt", "")
    if not prompt:
        return "Error: empty image prompt"
    # Return special marker — Agent Loop will handle actual generation
    return f"__IMAGE_GENERATION__|{prompt}"


def _exec_get_weather(args: dict, ctx: dict) -> str:
    """
    Signal to Agent Loop for weather. Returns special marker.
    Actual weather function lives in main bot code.
    """
    city = args.get("city", "")
    country = args.get("country_hint", "")
    forecast_days = args.get("forecast_days", 1)
    if not city:
        return "Error: empty city name"
    return f"__WEATHER__|{city}|{country}|{forecast_days}"


def _exec_remember_fact(args: dict, ctx: dict) -> str:
    """Save a fact to long-term memory."""
    fact = args.get("fact", "")
    user_id = ctx.get("user_id", 0)
    if not fact:
        return "Error: empty fact"
    if not user_id:
        return "Error: no user_id in context"
    
    success = save_memory(user_id, fact, source="user_request")
    if success:
        return f"Факт сохранён в долгосрочную память: '{fact}'"
    return "Не удалось сохранить факт в память."


def _exec_recall_memories(args: dict, ctx: dict) -> str:
    """Search long-term memory for relevant facts."""
    query = args.get("query", "")
    user_id = ctx.get("user_id", 0)
    if not query or not user_id:
        return "Воспоминания не найдены."
    
    memories = search_memories(user_id, query, top_k=5, threshold=0.4)
    if not memories:
        return "В долгосрочной памяти нет релевантных фактов по этому запросу."
    
    result = "Найденные воспоминания:\n"
    for m in memories:
        result += f"- {m['fact_text']} (релевантность: {m['similarity']})\n"
    return result


def _exec_draw_tarot(args: dict, ctx: dict) -> str:
    """Draw a random tarot card. Returns special marker for Agent Loop."""
    # This is handled via the special marker pattern
    return "__TAROT__"


def _exec_get_horoscope(args: dict, ctx: dict) -> str:
    """Generate horoscope. Returns special marker for Agent Loop."""
    sign = args.get("sign", "")
    if not sign:
        return "Error: no zodiac sign specified"
    return f"__HOROSCOPE__|{sign}"


def _exec_set_reminder(args: dict, ctx: dict) -> str:
    """Create a reminder in the database."""
    text = args.get("text", "")
    remind_at = args.get("remind_at", 0)
    human_time = args.get("human_time", "")
    user_id = ctx.get("user_id", 0)
    
    if not text or not remind_at or not user_id:
        return "Error: missing text, remind_at or user_id"
    
    # Sanity check: remind_at should be in the future
    if remind_at < time.time():
        return "Error: remind_at is in the past. Please calculate a future timestamp."
    
    # Limit: max 30 days ahead
    max_future = time.time() + 30 * 24 * 3600
    if remind_at > max_future:
        return "Error: reminder too far in the future (max 30 days)."
    
    reminder_id = create_reminder(user_id, text, remind_at)
    if reminder_id:
        return f"✅ Напоминание #{reminder_id} установлено: '{text}' — {human_time}."
    return "Не удалось создать напоминание."


def _exec_list_reminders(args: dict, ctx: dict) -> str:
    """List all pending reminders for the user."""
    user_id = ctx.get("user_id", 0)
    if not user_id:
        return "Error: no user_id"
    
    reminders = get_user_reminders(user_id, status="pending")
    if not reminders:
        return "У тебя нет активных напоминаний."
    
    import datetime
    tz = datetime.timezone(datetime.timedelta(hours=3))  # Minsk UTC+3
    
    result = f"Активные напоминания ({len(reminders)}):\n"
    for r in reminders:
        dt = datetime.datetime.fromtimestamp(r['remind_at'], tz=tz)
        time_str = dt.strftime('%d.%m.%Y %H:%M')
        result += f"  #{r['id']} — {r['reminder_text']} (⏰ {time_str})\n"
    return result


def _exec_cancel_reminder(args: dict, ctx: dict) -> str:
    """Cancel a reminder by ID."""
    reminder_id = args.get("reminder_id", 0)
    user_id = ctx.get("user_id", 0)
    
    if not reminder_id or not user_id:
        return "Error: missing reminder_id or user_id"
    
    success = db_cancel_reminder(reminder_id, user_id)
    if success:
        return f"✅ Напоминание #{reminder_id} отменено."
    return f"Напоминание #{reminder_id} не найдено или уже выполнено/отменено."
