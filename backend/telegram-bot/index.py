import json
import os
import psycopg2
from datetime import date, datetime
from typing import Dict, Any, Optional
import requests

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Telegram bot webhook handler for greeting card generation with daily limits
    Args: event - dict with httpMethod, body; context - object with request_id
    Returns: HTTP response with statusCode, headers, body
    '''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'isBase64Encoded': False,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    db_url = os.environ.get('DATABASE_URL')
    
    if not bot_token or not db_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'isBase64Encoded': False,
            'body': json.dumps({'error': 'Missing configuration'})
        }
    
    body_data = json.loads(event.get('body', '{}'))
    
    if not body_data.get('message'):
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'isBase64Encoded': False,
            'body': json.dumps({'ok': True})
        }
    
    message = body_data['message']
    
    if message.get('from', {}).get('is_bot', False):
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'isBase64Encoded': False,
            'body': json.dumps({'ok': True})
        }
    
    chat_id = message['chat']['id']
    telegram_id = message['from']['id']
    username = message['from'].get('username')
    first_name = message['from'].get('first_name', '')
    last_name = message['from'].get('last_name', '')
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    try:
        cur.execute(
            "SELECT id, generation_count, last_generation_date FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        user = cur.fetchone()
        
        if not user:
            cur.execute(
                "INSERT INTO users (telegram_id, username, first_name, last_name) VALUES (%s, %s, %s, %s) RETURNING id, generation_count, last_generation_date",
                (telegram_id, username, first_name, last_name)
            )
            user = cur.fetchone()
            conn.commit()
        
        user_id, generation_count, last_gen_date = user
        today = date.today()
        
        if last_gen_date != today:
            generation_count = 0
            cur.execute(
                "UPDATE users SET generation_count = 0, last_generation_date = %s WHERE id = %s",
                (today, user_id)
            )
            conn.commit()
        
        if 'text' in message:
            text = message['text']
            
            if text == '/start':
                send_message(bot_token, chat_id, 
                    f"Привет, {first_name}! 👋\n\n"
                    "Я генерирую открытки с бабушкиным юмором.\n\n"
                    "📸 Отправь мне фото, и я создам открытку.\n"
                    f"✨ Осталось генераций сегодня: {3 - generation_count}/3"
                )
            elif text == '/limit':
                send_message(bot_token, chat_id, 
                    f"📊 Твой лимит на сегодня:\n"
                    f"Использовано: {generation_count}/3\n"
                    f"Осталось: {3 - generation_count}/3"
                )
            else:
                send_message(bot_token, chat_id, "Отправь мне фото, чтобы создать открытку! 📸")
        
        elif 'photo' in message:
            if generation_count >= 3:
                send_message(bot_token, chat_id, 
                    "❌ Ты исчерпал лимит на сегодня (3/3).\n"
                    "Приходи завтра! 🌅"
                )
            else:
                send_message(bot_token, chat_id, "⏳ Генерирую открытку...")
                
                photo = message['photo'][-1]
                file_id = photo['file_id']
                
                file_response = requests.get(f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}")
                file_data = file_response.json()
                
                if file_data.get('ok'):
                    file_path = file_data['result']['file_path']
                    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                    
                    image_response = requests.get(file_url)
                    import base64
                    image_base64 = base64.b64encode(image_response.content).decode('utf-8')
                    
                    generation_response = requests.post(
                        'https://d5dt42a8m2fk8h6dgdj7.apigw.yandexcloud.net/generate-card',
                        json={'imageBase64': f"data:image/jpeg;base64,{image_base64}"},
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    gen_data = generation_response.json()
                    
                    if gen_data.get('success') and gen_data.get('imageUrl'):
                        cur.execute(
                            "UPDATE users SET generation_count = generation_count + 1, last_generation_date = %s, updated_at = %s WHERE id = %s",
                            (today, datetime.now(), user_id)
                        )
                        conn.commit()
                        
                        send_photo(bot_token, chat_id, gen_data['imageUrl'], 
                            f"✅ Готово!\n📊 Использовано: {generation_count + 1}/3")
                    else:
                        send_message(bot_token, chat_id, "❌ Ошибка генерации. Попробуй еще раз.")
                else:
                    send_message(bot_token, chat_id, "❌ Не удалось получить фото.")
        
    finally:
        cur.close()
        conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'isBase64Encoded': False,
        'body': json.dumps({'ok': True})
    }

def send_message(token: str, chat_id: int, text: str):
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={'chat_id': chat_id, 'text': text}
    )

def send_photo(token: str, chat_id: int, photo_url: str, caption: str):
    requests.post(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        json={'chat_id': chat_id, 'photo': photo_url, 'caption': caption}
    )