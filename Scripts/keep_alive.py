from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "I am alive. Telegram Assistant is running!"

def run():
    # Render или Heroku предоставляют порт через переменную окружения PORT
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """
    Запускает веб-сервер Flask в отдельном потоке, 
    чтобы бот мог параллельно отвечать на сообщения Telegram.
    """
    t = Thread(target=run)
    t.daemon = True
    t.start()
