# 🤖 Telegram AI Vision Assistant

[![English](https://img.shields.io/badge/lang-en-red.svg)](#-english)
[![Русский](https://img.shields.io/badge/lang-ru-blue.svg)](#-русский)

---

## 🇺🇸 English

![Status](https://img.shields.io/badge/Status-Ultra--Modern-brightgreen)
![Intelligence](https://img.shields.io/badge/Core-Llama_4_Scout-blueviolet)
![OCR](https://img.shields.io/badge/OCR-Gemma_4_31B-orange)
![Art](https://img.shields.io/badge/Art-Pollinations.ai-pink)

**Telegram AI Vision Assistant** is a high-performance hybrid assistant that combines the lightning speed of Llama 4 Scout with the unmatched accuracy of Gemma 4 31B for specialized tasks.

### ✨ Key Features

#### ⚖️ Hybrid Vision Architecture
The bot automatically routes tasks based on the image type:
- **General Photos:** Processed by the lightning-fast **Llama 4 Scout (17B/Groq)** for instant descriptions.
- **Handwritten Text & Complex OCR:** Handled by **Gemma 4 31B (OpenRouter Paid)** — a recognized expert in handwriting recognition and complex document structures.

#### 🎨 AI Art & Generation
Integration with multiple engines allows the bot to choose the best option for creating art:
- **Pollinations.ai:** Fast generation using Flux and Zimage models.
- **Pixazo AI (Gateway):** Professional gateway for the **FLUX-1-schnell** model, providing high detail and stability.
- **Together AI:** Backup channel for high-fidelity generation models.
- **Automatic Prompt Engineering:** The bot enhances user prompts before sending them to the neural network.

#### 🧠 Contextual Memory & Search
- **Memory System:** Remembers dialogue context and details from previously uploaded images.
- **Web Search:** Integrated with **Serper** to find real-time information on the web.
- **Voice Intelligence:** Full support for voice messages (STT/TTS).

### 🛠 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aicubik/Telegram_Voice_Bot.git
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure `Credentials.env`:**
   Create a file in the project root and add your keys:
   ```env
   TELEGRAM_BOT_TOKEN=your_token
   GROQ_API_KEY=your_key
   OPENROUTER_API_KEY=your_key
   SERPER_API_KEY=your_key
   POLLINATIONS_API_KEY=your_key
   PIXAZO_API_KEY=your_key
   ```

---

## 🇷🇺 Русский

**Telegram AI Vision Assistant** — это высокопроизводительный гибридный ассистент, сочетающий в себе скорость Llama 4 Scout и непревзойденную точность Gemma 4 31B для специализированных задач.

### ✨ Основные возможности

#### ⚖️ Гибридная архитектура зрения (AI Vision)
Бот автоматически маршрутизирует задачи в зависимости от типа изображения:
- **Обычные фото:** Обрабатываются молниеносной **Llama 4 Scout (17B/Groq)** для мгновенного описания.
- **Рукописный текст и сложный OCR:** Включается **Gemma 4 31B (OpenRouter Paid)** — признанный эксперт в распознавании почерка и сложных структур.

#### 🎨 Искусство и Генерация (AI Multimedia)
Интеграция с несколькими движками позволяет боту выбирать лучший вариант для создания артов:
- **Pollinations.ai:** Быстрая генерация моделей Flux и Zimage.
- **Pixazo AI (Gateway):** Профессиональный шлюз для модели **FLUX-1-schnell**, обеспечивающий высокую детализацию и стабильность.
- **Автоматическое улучшение промптов** перед отправкой нейросети.

#### 🧠 Контекстная память и Поиск
- **Memory System:** Бот помнит контекст диалога и детали из загруженных ранее изображений.
- **Web Search:** Интеграция с **Serper** позволяет боту искать актуальную информацию в интернете в реальном времени.
- **Voice Intelligence:** Полная поддержка голосовых сообщений (STT/TTS).

---

## 🛡 Security & Privacy

The project has undergone a full security audit. All API keys are stored in `Credentials.env`, which is automatically ignored by Git. History has been sanitized for safe public use.

---

*Developed with focus on quality and privacy.*
