import os
import time
import base64
import random
import tempfile
import telebot
from telebot import types
import requests as http_requests
from dotenv import load_dotenv
from openai import OpenAI
import re
from urllib.parse import quote
from keep_alive import keep_alive
import io
import pypdf
import docx
import csv
import openpyxl
import zlib
import phpserialize
import xlrd
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("⚠️ ddgs not installed, using HTML fallback only")

# 1. Загрузка конфигураций
load_dotenv('../Credentials.env')
load_dotenv('Credentials.env')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')
HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
POLLINATIONS_KEY = os.getenv('POLLINATIONS_API_KEY')
PIXAZO_KEY = os.getenv('PIXAZO_API_KEY')
TOGETHER_KEY = os.getenv('TOGETHER_API_KEY')

# Инициализация клиентов
bot = telebot.TeleBot(TELEGRAM_TOKEN or "dummy_token")

# 1. Groq (LPU Inference)
groq_client = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# 2. OpenRouter (Ultimate Fallback & Experts)
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

# 2. Память бота
user_memory = {}
MAX_HISTORY = 20

SYSTEM_PROMPT = (
    "Ты — полезный персональный ассистент. "
    "ВСЕГДА отвечай на русском языке, если пользователь не попросит иначе. "
    "Будь кратким, конкретным и дружелюбным. Избегай повторов и воды. "
    "Твой пользователь находится в Беларуси — учитывай это при ответах "
    "о ценах, валютах, новостях и законах, если не указано иное. "
    "Если в сообщении пользователя есть [Контекст из интернета], "
    "используй эту свежую информацию для ответа, но отвечай своими словами. "
    "При использовании данных из интернета кратко укажи это. "
    "Если пользователь отправил изображение, в истории будет его описание — "
    "учитывай его при ответах на последующие вопросы."
)

MYSTIC_PROMPT = (
    "Ты — мистический оракул и мастер Таро, потомственный астролог с глубоким знанием эзотерики. "
    "Обращайся к собеседнику на 'ты'. Говори загадочно, мудро и поэтично, "
    "используй метафоры и образы (свечи, туман, звёзды, лунный свет). "
    "ВСЕГДА отвечай на русском языке. "
    "Ты веришь в силу карт и звёзд, и даёшь глубокие, осмысленные интерпретации. "
    "Не говори, что ты ИИ. Ты — оракул, проводник между мирами."
)

# 2.1 Колода Таро — 22 Старших Аркана
MAJOR_ARCANA = [
    {"name": "Шут",               "en": "The Fool",            "num": "0"},
    {"name": "Маг",               "en": "The Magician",        "num": "I"},
    {"name": "Верховная Жрица",   "en": "The High Priestess",  "num": "II"},
    {"name": "Императрица",       "en": "The Empress",         "num": "III"},
    {"name": "Император",         "en": "The Emperor",         "num": "IV"},
    {"name": "Верховный Жрец",    "en": "The Hierophant",      "num": "V"},
    {"name": "Влюблённые",        "en": "The Lovers",          "num": "VI"},
    {"name": "Колесница",         "en": "The Chariot",         "num": "VII"},
    {"name": "Сила",              "en": "Strength",            "num": "VIII"},
    {"name": "Отшельник",         "en": "The Hermit",          "num": "IX"},
    {"name": "Колесо Фортуны",   "en": "Wheel of Fortune",    "num": "X"},
    {"name": "Справедливость",    "en": "Justice",             "num": "XI"},
    {"name": "Повешенный",        "en": "The Hanged Man",      "num": "XII"},
    {"name": "Смерть",            "en": "Death",               "num": "XIII"},
    {"name": "Умеренность",       "en": "Temperance",          "num": "XIV"},
    {"name": "Дьявол",            "en": "The Devil",           "num": "XV"},
    {"name": "Башня",             "en": "The Tower",           "num": "XVI"},
    {"name": "Звезда",            "en": "The Star",            "num": "XVII"},
    {"name": "Луна",              "en": "The Moon",            "num": "XVIII"},
    {"name": "Солнце",            "en": "The Sun",             "num": "XIX"},
    {"name": "Суд",               "en": "Judgement",           "num": "XX"},
    {"name": "Мир",               "en": "The World",           "num": "XXI"},
]

# 2.2 Знаки зодиака
ZODIAC_SIGNS = [
    {"name": "Овен",     "emoji": "♈", "en": "Aries"},
    {"name": "Телец",    "emoji": "♉", "en": "Taurus"},
    {"name": "Близнецы", "emoji": "♊", "en": "Gemini"},
    {"name": "Рак",      "emoji": "♋", "en": "Cancer"},
    {"name": "Лев",      "emoji": "♌", "en": "Leo"},
    {"name": "Дева",     "emoji": "♍", "en": "Virgo"},
    {"name": "Весы",     "emoji": "♎", "en": "Libra"},
    {"name": "Скорпион", "emoji": "♏", "en": "Scorpio"},
    {"name": "Стрелец",  "emoji": "♐", "en": "Sagittarius"},
    {"name": "Козерог",  "emoji": "♑", "en": "Capricorn"},
    {"name": "Водолей",  "emoji": "♒", "en": "Aquarius"},
    {"name": "Рыбы",     "emoji": "♓", "en": "Pisces"},
]

def get_memory(user_id):
    if user_id not in user_memory:
        user_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_memory[user_id]

def add_message_to_memory(user_id, role, content):
    memory = get_memory(user_id)
    memory.append({"role": role, "content": content})
    if len(memory) > MAX_HISTORY + 1:
        memory.pop(1)

# 3. Функции для работы с моделями

def generate_text_pollinations(messages):
    """Генерация текста через Pollinations AI (GPT-OSS 20B / openai-fast)."""
    try:
        # Используем openai-совместимый эндпоинт Pollinations если доступен, 
        # или просто прямой POST запрос для максимальной легкости.
        url = "https://text.pollinations.ai/"
        # Для Pollinations мы передаем последний запрос пользователя
        last_query = messages[-1]["content"]
        payload = {
            "messages": messages,
            "model": "openai-fast" # Авто-выбор лучшей модели (напр. GPT-OSS)
        }
        response = http_requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"⚠️ Pollinations Text failed: {e}")
    return None

def ask_llm_smart(messages, user_id=None):
    """
    Умная функция запроса к ИИ с автоматическим переключением провайдеров (Smart Fallback).
    Порядок 2026: Groq (Llama 4) -> Qwen3 (если код) -> OpenRouter (Llama 3.3 / Gemma 4) -> Pollinations.
    """
    query_text = messages[-1]["content"].lower()
    code_triggers = ["код", "script", "программ", "python", "js", "html", "сайт", "лендинг", "напиши на", "sql"]
    is_coding_task = any(t in query_text for t in code_triggers)

    providers = [
        {"name": "Groq (Llama 4)", "client": groq_client, "model": "meta-llama/llama-4-scout-17b-16e-instruct"},
        {"name": "OpenRouter (Llama 3.3)", "client": openrouter_client, "model": "meta-llama/llama-3.3-70b-instruct:free"},
        {"name": "OpenRouter (Gemma 4)", "client": openrouter_client, "model": "google/gemma-4-31b-it:free"}
    ]

    # Если задача кодинга, вставляем Qwen3 в начало (после основной попытки или сразу)
    if is_coding_task:
        qwen_provider = {"name": "Qwen3 Coder", "client": openrouter_client, "model": "qwen/qwen3-coder:free"}
        providers.insert(0, qwen_provider)
        if user_id:
            try: bot.send_message(user_id, "👨‍💻 *Переключаюсь в режим кодинга (Qwen3 Coder)...*", parse_mode="Markdown")
            except: pass

    for provider in providers:
        if not provider["client"].api_key:
            continue
            
        try:
            print(f"Trying provider: {provider['name']}...")
            completion = provider["client"].chat.completions.create(
                model=provider["model"],
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"⚠️ {provider['name']} failed: {e}")
            continue

    # Финальный сверхстабильный фоллбэк
    print("Trying Pollinations as final fallback...")
    final_res = generate_text_pollinations(messages)
    if final_res:
        return final_res
    
    return "⚠️ К сожалению, все магические каналы связи сейчас перегружены. Попробуй через минуту."

def analyze_image_groq(base64_image, user_question="Опиши подробно, что ты видишь на этом изображении."):
    """Анализ изображения через Groq Vision (быстрый)."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Отвечай на русском языке. {user_question}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }
    ]
    completion = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
    )
    return completion.choices[0].message.content

def analyze_image_openrouter(base64_image, user_question, model_id="google/gemma-4-31b-it"):
    """Анализ изображения через OpenRouter (Gemma 4 31B - Paid для точного OCR)."""
    messages = [
        {
            "role": "user",
                {"type": "text", "text": f"Ты — самый точный в мире эксперт по распознаванию рукописного текста (OCR). Пожалуйста, максимально точно перепиши текст с изображения, сохраняя структуру. Используй русский язык. ОЧЕНЬ ВАЖНО: не фантазируй, пиши только то, что видишь. {user_question}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }
    ]
    completion = openrouter_client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=0.3,
        max_tokens=2048,
        extra_headers={
            "HTTP-Referer": "https://github.com/aicubik/Telegram_Voice_Bot", # Идентификация для OpenRouter
            "X-Title": "Telegram OCR Bot",
        }
    )
    # Возвращаем текст и РЕАЛЬНОЕ имя модели, которое выбрал роутер
    return completion.choices[0].message.content, completion.model

def translate_prompt_for_image(user_prompt):
    """Скрытый перевод промпта пользователя на английский для генерации картинки."""
    messages = [
        {"role": "system", "content": (
            "You are a translator. Translate the user's image generation prompt to English. "
            "If no specific style is mentioned, add 'photorealistic, high quality, detailed' to the prompt. "
            "If a specific style IS mentioned (e.g. 'в стиле аниме', 'масляная живопись'), keep that style. "
            "Output ONLY the translated prompt, nothing else. No explanations."
        )},
        {"role": "user", "content": user_prompt}
    ]
    try:
        result = ask_llm_smart(messages)
        return result.strip()
    except Exception:
        # Если перевод не удался — используем оригинал
        return user_prompt

# --- Веб-поиск (DuckDuckGo, бесплатно, без ключа) ---

DEFAULT_REGION = "Беларусь"

def needs_web_search(query):
    """Определяет, нужен ли веб-поиск для ответа на вопрос."""
    q = query.lower()
    
    # Слишком короткий текст — не ищем
    if len(q.split()) < 3:
        return False
    
    # Категория 1: Прямой запрос на поиск
    if any(t in q for t in ["найди", "загугли", "поищи", "search", "гугл"]):
        return True
    
    # Категория 3: Кто/что это
    if any(t in q for t in ["кто такой", "кто такая", "что такое", "что за",
                             "расскажи про", "информация о", "что известно"]):
        return True
    
    # Категория 4: Фактчекинг
    if any(t in q for t in ["правда ли", "правда что", "это правда", "проверь"]):
        return True
    
    # Категория 5: Цены/продукты
    if any(t in q for t in ["сколько стоит", "цена на", "где купить", "обзор"]):
        return True
    
    # Категория 2: Время + тема (нужны ОБА)
    time_markers = ["сегодня", "вчера", "сейчас", "2025", "2026",
                    "последни", "свежи", "актуальн", "на данный момент"]
    info_topics = ["курс", "цена", "новост", "результат", "счёт",
                   "матч", "выбор", "закон", "событи", "произошл"]
    
    has_time = any(t in q for t in time_markers)
    has_topic = any(t in q for t in info_topics)
    if has_time and has_topic:
        return True
    
    return False

def localize_search_query(query):
    """Добавить региональный контекст (Беларусь) к поисковому запросу если нужно."""
    q_lower = query.lower()
    
    # Если регион уже указан — не трогаем
    regions = ["беларус", "росси", "украин", "казахстан", "польш",
               "сша", "usa", "europe", "европ", "мир", "минск", "москв",
               "киев", "варшав", "лондон", "берлин", "париж"]
    if any(r in q_lower for r in regions):
        return query
    
    # Темы, требующие региональной привязки
    regional_topics = [
        "курс", "валют", "доллар", "евро", "рубл",
        "цена", "стоимость", "стоит", "бензин", "топлив",
        "новост", "событи", "произошл",
        "закон", "указ", "постановлен", "выбор",
        "зарплат", "пенси", "пособи", "налог",
    ]
    
    if any(topic in q_lower for topic in regional_topics):
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
            print(f"⚠️ DDG HTML returned {resp.status_code}")
            return []
        
        # Парсим результаты без BeautifulSoup (regex)
        results = []
        # Ищем блоки результатов
        snippets = re.findall(
            r'class="result__a"[^>]*>([^<]+)</a>.*?class="result__snippet"[^>]*>(.*?)</span>',
            resp.text, re.DOTALL
        )
        for title, body in snippets[:3]:
            # Убираем HTML-теги из body
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
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        import json
        payload = json.dumps({
            "q": search_query,
            "gl": "by",
            "hl": "ru",
            "num": 3
        })
        resp = http_requests.post(url, headers=headers, data=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            organic = data.get("organic", [])
            
            results = []
            
            # Точные ответы
            answer = data.get("answerBox", {})
            if answer and "answer" in answer:
                results.append({"title": "Прямой ответ", "body": answer["answer"]})
            elif answer and "snippet" in answer:
                results.append({"title": "Краткий ответ", "body": answer["snippet"]})
            
            # Knowledge graph
            kg = data.get("knowledgeGraph", {})
            if kg and "description" in kg:
                results.append({"title": kg.get("title", "Факт"), "body": kg["description"]})

            # Обычная выдача
            for r in organic[:3]:
                if len(results) >= 4:
                    break
                results.append({"title": r.get("title", ""), "body": r.get("snippet", "")})
                
            return results
        else:
            print(f"⚠️ Serper API returned {resp.status_code}: {resp.text}")
            return []
    except Exception as e:
        print(f"⚠️ Serper search failed: {e}")
        return []

def perform_web_search(query):
    """Выполнить поиск через Serper.dev (с фоллбэком на DuckDuckGo)."""
    search_query = localize_search_query(query)
    print(f"🔍 Searching: {search_query}")
    
    # Цепочка: Serper → ddgs → HTML скрапинг
    results = _search_serper(search_query)
    
    if not results:
        print("🔄 Serper failed, trying DDGS library...")
        results = _search_ddgs(search_query)
        
    if not results:
        print("🔄 DDGS failed, trying HTML fallback...")
        results = _search_html_fallback(search_query)
    
    if not results:
        print("❌ All search methods failed")
        return ""
    
    context = "🔍 Результаты веб-поиска:\n"
    for i, r in enumerate(results, 1):
        context += f"{i}. {r['title']}: {r['body']}\n"
    return context

# --- Погода (Open-Meteo, бесплатно, без ключа) ---

WEATHER_CODES = {
    0: "☀️ Ясно", 1: "🌤️ Преимущественно ясно", 2: "⛅ Переменная облачность",
    3: "☁️ Пасмурно", 45: "🌫️ Туман", 48: "🌫️ Изморозь",
    51: "🌦️ Лёгкая морось", 53: "🌦️ Морось", 55: "🌧️ Сильная морось",
    61: "🌧️ Небольшой дождь", 63: "🌧️ Дождь", 65: "🌧️ Сильный дождь",
    71: "🌨️ Небольшой снег", 73: "🌨️ Снег", 75: "❄️ Сильный снегопад",
    77: "❄️ Снежные зёрна", 80: "🌧️ Ливень", 81: "🌧️ Сильный ливень",
    82: "⛈️ Шквалистый ливень", 85: "🌨️ Снегопад", 86: "❄️ Сильный снегопад",
    95: "⛈️ Гроза", 96: "⛈️ Гроза с градом", 99: "⛈️ Сильная гроза с градом",
}

def _geocode_city(city_name, country_hint=None):
    """Запрос к Open-Meteo Geocoding API с приоритетом Беларуси (если hint не указан)."""
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote(city_name)}&count=5&language=ru&format=json"
    geo_resp = http_requests.get(geo_url, timeout=10)
    if geo_resp.status_code != 200:
        return {}
    data = geo_resp.json()
    if "results" not in data or len(data["results"]) == 0:
        return data

    # Определяем приоритетную страну. Если пользователь не указал, по умолчанию Беларусь.
    hints = []
    if country_hint:
        hints.append(country_hint.lower())
        mapping = {
            "беларусь": "belarus", "белоруссия": "belarus", "рб": "belarus",
            "россия": "russia", "рф": "russia",
            "украина": "ukraine",
            "казахстан": "kazakhstan",
            "польша": "poland",
            "сша": "united states", "usa": "united states"
        }
        en_hint = mapping.get(country_hint.lower())
        if en_hint:
            hints.append(en_hint)
    else:
        hints = ["беларусь", "belarus"]
    
    # 1. Сначала ищем точное совпадение по приоритету/подсказке
    for place in data["results"]:
        place_country = place.get("country", "").lower()
        place_admin = place.get("admin1", "").lower()
        if any(h in place_country or h in place_admin for h in hints):
            return {"results": [place]}
    
    # 2. Если с приоритетом ничего не нашли, а пользователь НЕ указывал страну явно,
    # то возвращаем просто первый результат из списка.
    if not country_hint:
        return {"results": [data["results"][0]]}
        
    # 3. Если пользователь ЯВНО указал страну (hint), но в топ-5 её нет — возвращаем пустой результат.
    return {"results": []}

def _translate_city_to_english(city_text):
    """Снять склонение и перевести город на английский для точного поиска в Open-Meteo."""
    try:
        messages = [
            {"role": "system", "content": (
                "Переведи название города на английский язык (именительный падеж). "
                "Выведи ТОЛЬКО английское название города и больше ничего. "
                "Примеры: минске → Minsk, москве → Moscow, бобруйск → Babruysk, "
                "санкт-петербурге → Saint Petersburg"
            )},
            {"role": "user", "content": city_text}
        ]
        result = ask_llm_smart(messages)
        return result.strip().strip('"\'.,!?')
    except Exception:
        return city_text

def get_weather(city_name, country_hint=None):
    """Получить прогноз погоды для города через Open-Meteo (бесплатно)."""
    # 1. Геокодинг: Сначала переводим в английский, так как Open-Meteo плохо ищет кириллицу (например, Бобруйск)
    search_query = _translate_city_to_english(city_name)
    geo_data = _geocode_city(search_query, country_hint)
    
    # Если по английски почему-то не нашло, пробуем оригинал
    if "results" not in geo_data or len(geo_data["results"]) == 0:
        if search_query.lower() != city_name.lower():
            geo_data = _geocode_city(city_name, country_hint)
    
    if "results" not in geo_data or len(geo_data["results"]) == 0:
        return None, city_name  # Город не найден
    
    place = geo_data["results"][0]
    lat, lon = place["latitude"], place["longitude"]
    display_name = place.get("name", city_name)
    country = place.get("country", "")
    
    # 2. Погода: координаты → текущие данные + прогноз на сегодня
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,wind_speed_10m_max"
        f"&timezone=auto&forecast_days=1"
    )
    w_resp = http_requests.get(weather_url, timeout=10)
    if w_resp.status_code != 200:
        raise Exception(f"Ошибка погоды: {w_resp.status_code}")
    
    w = w_resp.json()
    cur = w["current"]
    day = w["daily"]
    
    weather_desc = WEATHER_CODES.get(cur.get("weather_code", 0), "🌡️ Нет данных")
    
    text = (
        f"🌤️ *Погода: {display_name}* ({country})\n\n"
        f"{weather_desc}\n\n"
        f"🌡️ Сейчас: *{cur['temperature_2m']}°C* (ощущается {cur['apparent_temperature']}°C)\n"
        f"📊 Мин / Макс: {day['temperature_2m_min'][0]}°C / {day['temperature_2m_max'][0]}°C\n"
        f"💧 Влажность: {cur['relative_humidity_2m']}%\n"
        f"💨 Ветер: {cur['wind_speed_10m']} км/ч (порывы до {cur['wind_gusts_10m']} км/ч)\n"
        f"🌧️ Осадки за день: {day['precipitation_sum'][0]} мм\n"
        f"🌅 Восход: {day['sunrise'][0][-5:]}  🌇 Закат: {day['sunset'][0][-5:]}"
    )
    return text, display_name

def _parse_city_country(raw):
    """Вспомогательная функция для разделения 'город страна' или 'город, страна'."""
    raw = raw.strip()
    # Пробуем разделить на город и страну/регион:
    # 'колки беларусь' → city='колки', country='беларусь'
    # 'москва' → city='москва', country=None
    parts = raw.rsplit(',', 1)  # "колки, беларусь"
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    
    # Пробуем разделить по пробелу — последнее слово может быть страной
    words = raw.split()
    if len(words) >= 2:
        known_countries = [
            'беларусь', 'белоруссия', 'россия', 'украина', 'казахстан',
            'польша', 'сша', 'англия', 'германия', 'франция', 'италия',
            'испания', 'турция', 'китай', 'япония', 'индия', 'аргентина',
            'бразилия', 'канада', 'австралия', 'мексика',
            'литва', 'латвия', 'эстония', 'грузия', 'армения', 'азербайджан',
            'узбекистан', 'молдова', 'таджикистан', 'киргизия',
            'usa', 'uk', 'belarus', 'russia', 'ukraine', 'poland', 'germany', 'france',
        ]
        last_word = words[-1].lower()
        if last_word in known_countries:
            city = ' '.join(words[:-1])
            return city, last_word
    return raw, None

def extract_city_from_text(text):
    """Извлечь название города и страну из текста. Возвращает (city, country_hint) или (None, None)."""
    import re
    text_clean = text.lower().strip().rstrip('?.!')
    
    patterns = [
        r'погод[аыуе]\s+(?:в|на|во)\s+(.+)',
        r'погод[аыуе]\s+(.+)',
        r'weather\s+(?:in\s+)?(.+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text_clean)
        if match:
            return _parse_city_country(match.group(1))
    return None, None

# --- Генерация изображений ---

def generate_image_legacy(prompt_en):
    """Генерация изображения через Pollinations.ai (бесплатно, без ключа)."""
    encoded_prompt = quote(prompt_en)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&enhance=false"
    response = http_requests.get(url, timeout=120)
    if response.status_code == 200:
        return response.content
    raise Exception(f"Legacy Pollinations failed: {response.status_code}")

def generate_image_pollinations_auth(prompt_en, model="zimage"):
    """Генерация через Pollinations.ai с API ключом."""
    if not POLLINATIONS_KEY:
        return generate_image_legacy(prompt_en)
    
    encoded_prompt = quote(prompt_en)
    url = f"https://gen.pollinations.ai/image/{encoded_prompt}?model={model}&width=1024&height=1024&seed={random.randint(0, 999999)}&nologo=true&enhance=false&key={POLLINATIONS_KEY}"
    response = http_requests.get(url, timeout=120)
    if response.status_code == 200:
        return response.content
    raise Exception(f"Pollinations Auth failed: {response.status_code}")

def generate_image_pixazo(prompt_en):
    """Генерация через Pixazo API (Flux-1-schnell) - Обновлено под 2026."""
    if not PIXAZO_KEY:
        raise Exception("PIXAZO_API_KEY не установлен")
    
    # В 2026 году Pixazo использует Unified Gateway
    url = "https://gateway.pixazo.ai/flux-1-schnell/v1/getData"
    headers = {
        "Ocp-Apim-Subscription-Key": PIXAZO_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt_en,
        "width": 1024,
        "height": 1024
    }
    
    response = http_requests.post(url, headers=headers, json=payload, timeout=120)
    if response.status_code == 200:
        data = response.json()
        media_url = data.get("output")
        if media_url and media_url.startswith("http"):
            # Скачиваем изображение по прямой ссылке
            img_res = http_requests.get(media_url, timeout=60)
            if img_res.status_code == 200:
                return img_res.content
            raise Exception(f"Pixazo double-get failed: {img_res.status_code}")
    raise Exception(f"Pixazo failed: {response.status_code} - {response.text}")

def generate_image_together(prompt_en):
    """Генерация через Together AI (Flux-schnell)."""
    if not TOGETHER_KEY:
        raise Exception("TOGETHER_API_KEY не установлен")
    
    url = "https://api.together.xyz/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {TOGETHER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "black-forest-labs/FLUX.1-schnell",
        "prompt": prompt_en,
        "width": 1024,
        "height": 1024,
        "steps": 4,
        "response_format": "b64_json"
    }
    response = http_requests.post(url, headers=headers, json=payload, timeout=120)
    if response.status_code == 200:
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            return base64.b64decode(data["data"][0]["b64_json"])
    raise Exception(f"Together AI failed: {response.status_code}")

def _generate_and_send_image(user_id, prompt, message, force_premium=False):
    """Умная генерация с фоллбэком."""
    bot.send_chat_action(user_id, 'upload_photo')
    status_msg = bot.reply_to(message, "🎨 Начинаю работу над шедевром, подождите...")

    try:
        prompt_en = translate_prompt_for_image(prompt)
        image_bytes = None
        used_engine = ""
        
        generators = [
            {"name": "Pollinations (zimage)", "func": lambda p: generate_image_pollinations_auth(p, "zimage")},
            {"name": "Pollinations (flux)", "func": lambda p: generate_image_pollinations_auth(p, "flux")},
            {"name": "Pixazo (Flux)", "func": generate_image_pixazo},
            {"name": "Together AI (Flux)", "func": generate_image_together}
        ]

        for i, gen in enumerate(generators):
            try:
                if i > 0:
                    bot.edit_message_text(
                        f"🎨 Канал {generators[i-1]['name']} занят, пробую {gen['name']}...",
                        user_id, status_msg.message_id
                    )
                
                print(f"Trying image generator: {gen['name']}...")
                image_bytes = gen["func"](prompt_en)
                if image_bytes:
                    used_engine = gen["name"]
                    break
            except Exception as e:
                print(f"⚠️ {gen['name']} failed: {e}")
                continue

        if image_bytes:
            caption = f"🎨 По запросу: _{prompt}_ [{used_engine}]"
            safe_send_photo(user_id, image_bytes, caption=caption)
            add_message_to_memory(user_id, "user", f"[Запрос на картинку: {prompt}]")
            add_message_to_memory(user_id, "assistant", f"[Картинка сгенерирована ({used_engine})]")
        else:
            bot.reply_to(message, "😔 Все генераторы сейчас перегружены. Попробуй позже.")

        bot.delete_message(user_id, status_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка в мастерской: {e}")

# 4. Обработчики Telegram

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я твой лично ИИ-помощник.\n\n"
        "💬 *Текст* — задай любой вопрос\n"
        "🎤 *Голос* — отправь голосовое сообщение\n"
        "📷 *Фото* — отправь картинку, я опишу что на ней\n"
        "🎨 *Рисование* — /draw или 'Нарисуй ...'\n"
        "🔮 *Таро* — /tarot для гадания\n"
        "⭐ *Гороскоп* — /horoscope\n"
        "🌤️ *Погода* — /weather Москва или 'погода в Минске'\n"
        "🌐 *Поиск* — 'найди', 'курс доллара', 'новости'\n"
        "🧹 *Очистка* — /clear для сброса контекста"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")
    user_memory[message.chat.id] = [{"role": "system", "content": SYSTEM_PROMPT}]

@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_memory[message.chat.id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    bot.reply_to(message, "🧹 Контекст диалога очищен.")

@bot.message_handler(commands=['draw', 'flux'])
def handle_draw_command(message):
    user_id = message.chat.id
    prompt = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not prompt:
        bot.reply_to(message, "✏️ Укажи описание после команды. Пример: `/draw кот в космосе`", parse_mode="Markdown")
        return
    _generate_and_send_image(user_id, prompt, message)

@bot.message_handler(commands=['weather'])
def handle_weather_command(message):
    user_id = message.chat.id
    raw_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not raw_text:
        bot.reply_to(message, "🌤️ Укажи город. Пример: `/weather Москва` или `/weather Колки Беларусь`", parse_mode="Markdown")
        return
    bot.send_chat_action(user_id, 'typing')
    
    city, country = _parse_city_country(raw_text)
    try:
        weather_text, _ = get_weather(city, country)
        if weather_text:
            safe_send_message(user_id, weather_text)
        else:
            bot.reply_to(message, f"🔍 Город *{city}* не найден. Попробуй другое название.", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка погоды: {e}")

@bot.message_handler(commands=['tarot'])
def handle_tarot_command(message):
    user_id = message.chat.id
    bot.send_chat_action(user_id, 'typing')
    card = random.choice(MAJOR_ARCANA)
    is_reversed = random.choice([True, False])
    position = "в перевёрнутом положении" if is_reversed else "в прямом положении"
    reversed_tag = " (Перевёрнутая)" if is_reversed else ""
    status_msg = bot.reply_to(message, "🔮 Карты перемешиваются...")

    try:
        image_bytes = None
        try:
            card_prompt = f"Mystical tarot card '{card['en']}', Major Arcana, occult style, detailed illustration, {'reversed' if is_reversed else ''}"
            image_bytes = generate_image_pollinations_auth(card_prompt, "flux")
        except: pass

        interpretation_messages = [
            {"role": "system", "content": MYSTIC_PROMPT},
            {"role": "user", "content": f"Я вытянул карту Таро: {card['name']} {position}. Дай интерпретацию."}
        ]
        interpretation = ask_llm_smart(interpretation_messages)
        bot.delete_message(user_id, status_msg.message_id)

        caption = f"🃏 *{card['name']}{reversed_tag}*\n\n🔮 {interpretation}"
        if image_bytes:
            safe_send_photo(user_id, image_bytes, caption=caption)
        else:
            safe_send_message(user_id, caption)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка таро: {e}")

@bot.message_handler(commands=['horoscope'])
def handle_horoscope_command(message):
    user_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(text=f"{s['emoji']} {s['name']}", callback_data=f"horo_{s['en']}") for s in ZODIAC_SIGNS]
    markup.add(*buttons)
    bot.send_message(user_id, "⭐ *Выбери знак зодиака:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('horo_'))
def handle_horoscope_callback(call):
    user_id = call.message.chat.id
    sign_en = call.data.replace('horo_', '')
    bot.edit_message_text(f"⭐ Составляю прогноз...", user_id, call.message.message_id)
    try:
        horo_messages = [{"role": "system", "content": MYSTIC_PROMPT}, {"role": "user", "content": f"Гороскоп для {sign_en} на сегодня."}]
        text = ask_llm_smart(horo_messages)
        safe_send_message(user_id, text)
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка гороскопа: {e}")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    bot.send_chat_action(user_id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        img_base64 = base64.b64encode(downloaded_file).decode('utf-8')
        
        # Подпись к фото или стандартный вопрос
        user_question = message.caption if message.caption else "Опиши подробно, что ты видишь на этом изображении."
        
        # ЛОГИКА ВЫБОРА МОДЕЛИ
        ocr_keywords = ["текст", "рукописн", "почерк", "прочитай", "расшифруй", "написано", "что здесь"]
        is_ocr_task = any(k in user_question.lower() for k in ocr_keywords)
        
        description = ""
        used_model = "Llama 4 Scout (Groq)"
        
        if is_ocr_task:
            msg_status = bot.reply_to(message, "🔍 Анализирую почерк с помощью Gemma 4 31B...")
            try:
                description, real_model = analyze_image_openrouter(img_base64, user_question)
                used_model = f"Gemma 4 31B (Paid: {real_model})"
                bot.delete_message(user_id, msg_status.message_id)
            except Exception as e:
                error_msg = str(e)
                print(f"OpenRouter Error: {error_msg}")
                bot.edit_message_text(f"⚠️ Ошибка OpenRouter ({error_msg[:50]}...), использую резервную Llama...", user_id, msg_status.message_id)
                description = analyze_image_groq(img_base64, user_question)
                used_model = "Llama 4 Scout (Groq - Fallback)"
                time.sleep(2)
                bot.delete_message(user_id, msg_status.message_id)
        else:
            description = analyze_image_groq(img_base64, user_question)
        
        # Сохраняем в память
        img_memory_text = f"[Пользователь прислал фото ({used_model})]: {user_question}"
        add_message_to_memory(user_id, "user", img_memory_text)
        add_message_to_memory(user_id, "assistant", f"[Содержимое фото]: {description}")
        
        safe_send_message(user_id, f"🔍 (Модель: {used_model})\n\n{description}", reply_to_message_id=message.message_id)
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка при распознавании фото: {e}")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.chat.id
    bot.send_chat_action(user_id, 'record_audio')
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio:
            temp_audio.write(downloaded_file)
            temp_path = temp_audio.name
        with open(temp_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(file=(temp_path, audio_file.read()), model="whisper-large-v3-turbo")
        query = transcription.text
        os.remove(temp_path)
        safe_send_message(user_id, f"🎤 *Распознано:* _{query}_", reply_to_message_id=message.message_id)
        message.text = query
        handle_text(message)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка голоса: {e}")

def safe_send_message(chat_id, text, **kwargs):
    """Безопасная отправка: сначала Markdown, при ошибке — plain text, при длинном — частями."""
    if len(text) > 4096:
        # Длинный текст — разбиваем на части, отправляем без Markdown
        for i in range(0, len(text), 4096):
            try:
                bot.send_message(chat_id, text[i:i+4096], **(kwargs if i == 0 else {}))
            except Exception:
                pass
        return
    try:
        bot.send_message(chat_id, text, parse_mode="Markdown", **kwargs)
    except Exception:
        try:
            bot.send_message(chat_id, text, **kwargs)
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Не удалось отправить ответ: {e}")

def safe_send_photo(chat_id, photo_bytes, caption, **kwargs):
    """Безопасная отправка фото с подписью: сначала Markdown, при ошибке — plain text."""
    # Telegram ограничивает caption до 1024 символов
    if len(caption) > 1024:
        caption = caption[:1021] + "..."
    try:
        bot.send_photo(chat_id, photo_bytes, caption=caption, parse_mode="Markdown", **kwargs)
    except Exception:
        # Убираем Markdown-символы и обрезаем для безопасности
        cleaned_caption = caption.replace("*", "").replace("_", "").replace("`", "")
        if len(cleaned_caption) > 1024:
            cleaned_caption = cleaned_caption[:1021] + "..."
        bot.send_photo(chat_id, photo_bytes, caption=cleaned_caption, **kwargs)

def _bpt_traverse(node, depth=0):
    text = ""
    prefix = "  " * depth
    if isinstance(node, dict):
        new_node = {}
        for k, v in node.items():
            key_str = k.decode('utf-8', errors='ignore') if isinstance(k, bytes) else str(k)
            new_node[key_str] = v
            
        b_type = ""
        if 'Type' in new_node and isinstance(new_node['Type'], bytes): b_type = new_node['Type'].decode('utf-8', errors='ignore')
        b_name = ""
        if 'Name' in new_node and isinstance(new_node['Name'], bytes): b_name = new_node['Name'].decode('utf-8', errors='ignore')
        
        if b_type or b_name:
            text += f"{prefix}[Блок: {b_type}] {b_name}\n"
            
        if 'Properties' in new_node and isinstance(new_node['Properties'], dict):
            props = new_node['Properties']
            for pk, pv in props.items():
                k_str = pk.decode('utf-8', errors='ignore') if isinstance(pk, bytes) else str(pk)
                if isinstance(pv, bytes):
                    v_str = pv.decode('utf-8', errors='ignore')
                    if len(v_str) > 2 and not v_str.isnumeric():
                        text += f"{prefix}  - {k_str}: {v_str[:200]}\n"
                        
        for pk, pv in new_node.items():
            if isinstance(pv, (dict, list, tuple)):
                if pk == 'Children':
                    text += _bpt_traverse(pv, depth+1)
                else:
                    text += _bpt_traverse(pv, depth)
                    
    elif isinstance(node, (list, tuple)):
        vs = list(node.values()) if hasattr(node, 'values') else node
        for item in vs:
            text += _bpt_traverse(item, depth)
            
    return text

def extract_text_from_document(file_bytes, file_name):
    """Извлекает текст из PDF, DOCX или TXT, с лимитом 20,000 символов."""
    ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
    text = ""
    try:
        if ext in ['txt', 'md']:
            text = file_bytes.decode('utf-8', errors='replace')
        elif ext == 'pdf':
            pdf = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif ext == 'docx':
            doc = docx.Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"
            # Извлекаем таблицы (важно для пользователя)
            for table in doc.tables:
                text += "\n[Таблица]:\n"
                for row in table.rows:
                    row_text = " | ".join([cell.text.replace('\n', ' ').strip() for cell in row.cells])
                    text += row_text + "\n"
                text += "\n"
        elif ext == 'csv':
            # Читаем CSV
            decoded_content = file_bytes.decode('utf-8', errors='replace').splitlines()
            reader = csv.reader(decoded_content)
            text += "[Таблица CSV]:\n"
            for row in reader:
                text += " | ".join(row) + "\n"
        elif ext == 'xlsx':
            # Читаем XLSX (Excel)
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                text += f"\n[Лист Excel: {sheet_name}]:\n"
                for row in sheet.iter_rows(values_only=True):
                    # Преобразуем значения в строки, None заменяем на пустую строку
                    row_text = " | ".join([str(cell).replace('\n', ' ').strip() if cell is not None else "" for cell in row])
                    if row_text.replace(" | ", "").strip(): # пропускаем совсем пустые строки
                        text += row_text + "\n"
        elif ext == 'xls':
            # Читаем старый XLSX (Excel 97-2003)
            wb = xlrd.open_workbook(file_contents=file_bytes)
            for sheet in wb.sheet_names():
                s = wb.sheet_by_name(sheet)
                text += f"\n[Лист Excel (old): {sheet}]:\n"
                for row_idx in range(s.nrows):
                    row_values = s.row_values(row_idx)
                    row_text = " | ".join([str(cell).replace('\n', ' ').strip() if cell != "" else "" for cell in row_values])
                    if row_text.replace(" | ", "").strip():
                        text += row_text + "\n"
        elif ext == 'bpt':
            # Читаем файл-шаблон Bitrix24
            dec = zlib.decompress(file_bytes)
            parsed = phpserialize.loads(dec)
            text += "[Bitrix24 Business Process Template]\n\n"
            text += "--- ПЕРЕМЕННЫЕ И ПАРАМЕТРЫ ---\n"
            if b'VARIABLES' in parsed and isinstance(parsed[b'VARIABLES'], dict):
               for k,v in parsed[b'VARIABLES'].items():
                   if isinstance(v, dict) and b'Name' in v:
                      text += f"Variables: {v[b'Name'].decode('utf-8', errors='ignore')}\n"
                      
            text += "\n--- ШАГИ БИЗНЕС-ПРОЦЕССА ---\n"
            if b'TEMPLATE' in parsed:
                text += _bpt_traverse(parsed[b'TEMPLATE'])
        else:
            return None
    except Exception as e:
        print(f"Error parsing {file_name}: {e}")
        return None
    
    return text[:20000]

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.chat.id
    
    # Ограничение Telegram для ботов = 20 MB
    if message.document.file_size > 20 * 1024 * 1024:
        bot.send_message(user_id, "📁 Файл слишком большой. Телеграм разрешает скачивать файлы только до 20 МБ.")
        return
        
    ext = message.document.file_name.lower().split('.')[-1] if '.' in message.document.file_name else ''
    allowed_exts = ['pdf', 'docx', 'txt', 'md', 'csv', 'xlsx', 'xls', 'bpt']
    if ext not in allowed_exts:
        bot.send_message(user_id, f"📁 Формат не поддерживается. Я понимаю: {', '.join(allowed_exts).upper()}.")
        return

    msg = bot.send_message(user_id, "⏳ Читаю документ, подожди секунду...")
    try:
        # Скачиваем файл
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Парсим текст
        text = extract_text_from_document(downloaded_file, message.document.file_name)
        
        if not text or not text.strip():
            bot.edit_message_text("❌ Не удалось извлечь текст из документа (возможно, он пустой или содержит только картинки).", chat_id=user_id, message_id=msg.message_id)
            return
            
        # Добавляем в контекст
        doc_info = f"[ДОКУМЕНТ: {message.document.file_name}]\n{text}"
        
        memory = get_memory(user_id)
        add_message_to_memory(user_id, "user", doc_info)
            
        if message.caption:
            add_message_to_memory(user_id, "user", message.caption)
            bot.edit_message_text(f"✅ Документ прочитан! Обрабатываю твой запрос: *{message.caption[:50]}...*", chat_id=user_id, message_id=msg.message_id, parse_mode="Markdown")
            
            bot.send_chat_action(user_id, 'typing')
            response = ask_llm_smart(get_memory(user_id), user_id=user_id)
            
            safe_send_message(user_id, response)
            add_message_to_memory(user_id, "assistant", response)
        else:
            bot.edit_message_text(f"✅ Я прочел документ *{message.document.file_name}* ({len(text)} символов). О чем хочешь узнать?", chat_id=user_id, message_id=msg.message_id, parse_mode="Markdown")
            
    except Exception as e:
        print(f"Doc error: {e}")
        bot.edit_message_text(f"❌ Ошибка при чтении документа: {e}", chat_id=user_id, message_id=msg.message_id)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    query = message.text
    query_lower = query.lower()
    
    draw_triggers = ["нарисуй", "изобрази", "картинка", "сгенерируй", "фото", "создай"]
    if any(trigger in query_lower for trigger in draw_triggers):
        _generate_and_send_image(user_id, query, message)
        return

    # Триггер на погоду: "погода в Москве", "какая погода в Минске"
    if "погод" in query_lower:
        city, country = extract_city_from_text(query)
        if city:
            bot.send_chat_action(user_id, 'typing')
            try:
                weather_text, _ = get_weather(city, country)
                if weather_text:
                    safe_send_message(user_id, weather_text)
                else:
                    bot.reply_to(message, f"🔍 Город *{city}* не найден.", parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"⚠️ Ошибка погоды: {e}")
            return

    bot.send_chat_action(user_id, 'typing')
    
    # Веб-поиск: проверяем, нужна ли свежая информация
    search_context = ""
    if needs_web_search(query):
        search_context = perform_web_search(query)
        if search_context:
            print(f"🔍 Web search triggered for: {query[:50]}")
    
    # Добавляем в память с контекстом поиска (если есть)
    if search_context:
        enriched_query = f"{query}\n\n[Контекст из интернета]:\n{search_context}"
        add_message_to_memory(user_id, "user", enriched_query)
    else:
        add_message_to_memory(user_id, "user", query)
    
    response = ask_llm_smart(get_memory(user_id), user_id=user_id)
    safe_send_message(user_id, response)
    add_message_to_memory(user_id, "assistant", response)

if __name__ == "__main__":
    print("Бот запускается...")
    keep_alive()  # Открываем порт для Render health check
    bot.remove_webhook()
    bot.polling(none_stop=True)
