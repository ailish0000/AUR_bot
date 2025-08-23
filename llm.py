# llm.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def limit_response_length(response: str, max_length: int = 999) -> str:
    """Ограничивает длину ответа до указанного количества символов"""
    if len(response) <= max_length:
        return response
    
    # Обрезаем до максимальной длины, сохраняя целые слова
    truncated = response[:max_length]
    
    # Ищем последний пробел или знак препинания
    last_space = truncated.rfind(' ')
    last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    last_break = max(last_space, last_punct)
    
    if last_break > max_length * 0.8:  # Если нашли хорошее место для обрезки
        truncated = truncated[:last_break + 1]
    else:
        # Если не нашли хорошего места, обрезаем по пробелу
        truncated = truncated[:last_space] if last_space > 0 else truncated
    
    # Добавляем индикатор обрезки
    truncated = truncated.strip()
    if not truncated.endswith(('.', '!', '?')):
        truncated += '...'
    
    # Финальная проверка - если все еще превышает лимит, жестко обрезаем
    if len(truncated) > max_length:
        truncated = truncated[:max_length-3] + "..."
    
    return truncated

def ask_llm(question: str, context: str) -> str:
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://t.me/YourBotNameBot",
                "X-Title": "Aurora Bot"
            },
            json={
                "model": "qwen/qwen-2.5-coder-32b-instruct:free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты — Наталья Кумасинская, мама двоих сыновей, эксперт по продуктам Авроры. "
                            "Ты делишься своим личным опытом. Говори тёпло, доверительно, как подруга, "
                            "но всегда опирайся только на факты из предоставленной информации. "
                            "Не выдумывай. Если не знаешь — скажи: 'Уточните, пожалуйста, я проверю'."
                            "ОТВЕТ ДОЛЖЕН БЫТЬ КРАТКИМ (до 800 символов)."
                            "Если информации недостаточно, извинись и предложи обратиться к консультанту Наталье."
                            "В конце предложи 2-3 дополнительных вопроса, которые пользователь может задать (например: 'Могу рассказать о пользе облепихи', 'Подробнее о составе', 'Как правильно принимать')."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Вопрос: {question}\n\nДанные из базы знаний:\n{context}"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 400  # Уменьшаем для более коротких ответов
            }
        )
        result = response.json()
        answer = result['choices'][0]['message']['content'].strip()
        
        # Ограничиваем длину ответа
        return limit_response_length(answer)
    except Exception as e:
        return f"Извините, сейчас не могу ответить. Ошибка: {str(e)}"