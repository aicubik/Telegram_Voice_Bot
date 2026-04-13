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

### 🎨 Генерация изображений через Pollinations.ai
Интеграция с мощным API **Pollinations.ai** позволяет создавать профессиональные арты прямо в чате:
- Используются современные модели (например, **Flux**, **Zimage**).
- Прямая генерация по текстовому описанию.

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
  - **Pollinations.ai:** Генерация изображений
  - **Serper:** Реал-тайм поиск

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
   SERPER_API_KEY=your_key
   POLLINATIONS_API_KEY=your_key
   ```

---

## 🛡 Безопасность

Проект прошел полный аудит безопасности. Все API-ключи вынесены в `Credentials.env`, который автоматически игнорируется системой контроля версий. История Git очищена от всех следов разработки для безопасного публичного использования.

---

*Разработано с заботой о качестве и приватности.*
