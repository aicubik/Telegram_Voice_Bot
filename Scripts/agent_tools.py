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
from memory_manager import (
    save_memory, search_memories, jina_search, jina_read_url,
    get_all_memories, clear_user_memories
)

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
                "Get the current weather forecast for a specific city. "
                "Use when the user asks about weather, temperature, rain, wind, etc. "
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
                "Draw a random Tarot card and generate its mystical interpretation. "
                "Use when the user asks for a tarot reading, fortune telling, or card guidance."
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
    }
    
    executor = executors.get(tool_name)
    if not executor:
        return f"Error: Unknown tool '{tool_name}'"
    
    try:
        return executor(arguments, context)
    except Exception as e:
        return f"Error executing {tool_name}: {e}"


# --- Individual Executors ---

def _exec_search_web(args: dict, ctx: dict) -> str:
    """Execute web search via Jina, with fallback to Serper."""
    query = args.get("query", "")
    if not query:
        return "Error: empty search query"
    
    # Try Jina Search first
    result = jina_search(query, max_results=3)
    
    # Fallback to Serper if Jina fails
    if not result:
        result = _serper_search_fallback(query)
    
    return result if result else "Поиск не дал результатов."


def _serper_search_fallback(query: str) -> str:
    """Fallback search via Serper.dev API."""
    import requests as http_requests
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return ""
    try:
        resp = http_requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "by", "hl": "ru", "num": 3},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            answer = data.get("answerBox", {})
            if answer and "answer" in answer:
                results.append(f"Прямой ответ: {answer['answer']}")
            for r in data.get("organic", [])[:3]:
                results.append(f"- {r.get('title', '')}: {r.get('snippet', '')}")
            return "\n".join(results) if results else ""
        return ""
    except Exception:
        return ""


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
    if not city:
        return "Error: empty city name"
    return f"__WEATHER__|{city}|{country}"


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
