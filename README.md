# 🤖 Telegram AI Vision Assistant

![Status](https://img.shields.io/badge/Status-Ultra--Modern-brightgreen)
![Intelligence](https://img.shields.io/badge/Core-Llama_4_Scout-blueviolet)
![OCR](https://img.shields.io/badge/OCR-Gemma_4_31B-orange)
![Art](https://img.shields.io/badge/Art-Pollinations.ai-pink)

**Telegram AI Vision Assistant** — это высокопроизводительный гибридный ассистент, сочетающий в себе скорость Llama 4 Scout и непревзойденную точность Gemma 4 31B для специализированных задач.

---

## ✨ Основные возможности

### ⚖️ Гибридная архитектура зрения (AI Vision)
Бот автоматически маршрутизирует задачи в зависимости от типа изображения:
- **Обычные фото:** Обрабатываются молниеносной **Llama 4 Scout (17B/Groq)** для мгновенного описания.
- **Рукописный текст и сложный OCR:** Включается **Gemma 4 31B (OpenRouter Paid)** — признанный эксперт в распознавании почерка и сложных структур.

### 🎨 Искусство и Генерация (AI Multimedia)
Интеграция с несколькими движками позволяет боту выбирать лучший вариант для создания артов:
*   **Pollinations.ai:** Быстрая генерация моделей Flux и Zimage.
*   **Pixazo AI (Gateway):** Профессиональный шлюз для модели **Flux-1-schnell**, обеспечивающий высокую детализацию и стабильность.
*   **Together AI:** Резервный канал для тяжелых моделей генерации.
*   Автоматическое улучшение промптов перед отправкой нейросети.

### 🧠 Контекстная память и Поиск
- **Memory System:** Бот помнит контекст диалога и детали из загруженных ранее изображений.
- **Web Search:** Интеграция с **Serper** позволяет боту искать актуальную информацию в интернете в реальном времени.
- **Voice Intelligence:** Полная поддержка голосовых сообщений (STT/TTS).

---

## 🚀 Технологический стек

- **Язык:** Python 3.10+
- **Framework:** `pyTelegramBotAPI` (Telebot)
- **Providers:**
  - **Groq:** Llama 4 Scout (Основная логика)
  - **OpenRouter:** Gemma 4 31B (OCR Эксперт)
  - **Image Gen (Fast):** Pollinations.ai (Платформа для открытой и быстрой генерации изображений)
  - **Image Gen (Pro):** Pixazo AI (Высококачественный Flux-1-schnell через Unified Gateway)
  - **Real-time Web:** Serper (JSON-API для Google Search)

---

## 🛠 Установка и настройка

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/your-repo/Telegram_Voice_Bot.git
   ```
2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Настройте `Credentials.env`:**
   Создайте файл в корне проекта и добавьте ключи:
   ```env
   TELEGRAM_BOT_TOKEN=your_token
   GROQ_API_KEY=your_key
   OPENROUTER_API_KEY=your_key
   SERPER_API_KEY=xxx...
   POLLINATIONS_API_KEY=sk_xxx...
   PIXAZO_API_KEY=xxx...
   ```

---

## 🛡 Безопасность

Проект прошел полный аудит безопасности. Все API-ключи вынесены в `Credentials.env`, который автоматически игнорируется системой контроля версий. История Git очищена от всех следов разработки для безопасного публичного использования.

---

*Разработано с заботой о качестве и приватности.*
