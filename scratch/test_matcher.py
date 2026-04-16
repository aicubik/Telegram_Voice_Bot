import re
text = "какие сегодня фильмы идут в кинотеатрах минска, расписание сеансов"
user_prompt_only = re.split(r"\[Из долгосрочной памяти|Текущее время:", text)[0].lower()
code_triggers = ["код", "script", "программ", "python", "js", "html", "сайт", "лендинг", "напиши на", "sql"]

for t in code_triggers:
    if t in user_prompt_only:
        print(f"MATCHED: {t}")
