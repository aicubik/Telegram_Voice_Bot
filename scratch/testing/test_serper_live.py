import os
import json
import requests
from dotenv import load_dotenv

# Загружаем ключи из Credentials.env
load_dotenv('Credentials.env')
key = os.getenv('SERPER_API_KEY')

print(f"Ключ загружен: {bool(key)}")
print(f"Отправляю запрос к Serper.dev...")

url = 'https://google.serper.dev/search'
headers = {
    'X-API-KEY': key,
    'Content-Type': 'application/json'
}
payload = {
    'q': 'курс доллара Беларусь',
    'gl': 'by',
    'hl': 'ru',
    'num': 3
}

resp = requests.post(url, headers=headers, json=payload)
print(f"Статус ответа: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    
    # Прямой факт (если гугл сразу ответил цифрой)
    kg = data.get('knowledgeGraph', {})
    if kg:
        print(f"\n✅ Факт из Гугла: {kg.get('title')} - {kg.get('description', '')}")
        
    answer = data.get('answerBox', {})
    if answer:
        print(f"\n✅ Прямой ответ Гугла: {answer.get('answer', answer.get('snippet', ''))}")
        
    print("\nТоп 3 органических результата:")
    for i, res in enumerate(data.get('organic', [])[:3], 1):
        print(f"{i}. {res.get('title')}\n   {res.get('snippet')}")
else:
    print(f"Ошибка: {resp.text}")
