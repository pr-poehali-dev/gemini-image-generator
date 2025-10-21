import json
import os
import psycopg2
from datetime import date, datetime
from typing import Dict, Any, Optional
import requests
import time

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
                funny_messages = [
                    "⏳ Бабушка подбирает рамочку...",
                    "🌸 Добавляем цветочки и блёстки...",
                    "💐 Бабуля выбирает лучшие пожелания...",
                    "✨ Украшаем открытку с любовью...",
                    "🎨 Наносим бабушкин шарм...",
                    "💝 Добавляем теплоты и уюта..."
                ]
                
                status_msg = send_message_return(bot_token, chat_id, funny_messages[0])
                message_id = status_msg.get('result', {}).get('message_id') if status_msg else None
                
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
                    
                    try:
                        generation_response = requests.post(
                            'https://d5dt42a8m2fk8h6dgdj7.apigw.yandexcloud.net/generate-card',
                            json={'imageBase64': f"data:image/jpeg;base64,{image_base64}"},
                            headers={'Content-Type': 'application/json'},
                            timeout=60
                        )
                        
                        gen_data = generation_response.json()
                        
                        if gen_data.get('success') and gen_data.get('imageUrl'):
                            cur.execute(
                                "UPDATE users SET generation_count = generation_count + 1, last_generation_date = %s, updated_at = %s WHERE id = %s",
                                (today, datetime.now(), user_id)
                            )
                            conn.commit()
                            
                            if message_id:
                                delete_message(bot_token, chat_id, message_id)
                            
                            send_photo(bot_token, chat_id, gen_data['imageUrl'], 
                                f"✅ Готово!\n📊 Использовано: {generation_count + 1}/3")
                        else:
                            if message_id:
                                edit_message(bot_token, chat_id, message_id, "❌ Не удалось создать открытку. Попробуйте еще раз!")
                            else:
                                send_message(bot_token, chat_id, "❌ Не удалось создать открытку. Попробуйте еще раз!")
                    
                    except requests.exceptions.Timeout:
                        if message_id:
                            edit_message(bot_token, chat_id, message_id, "⏱ Генерация заняла слишком много времени. Попробуйте еще раз!")
                        else:
                            send_message(bot_token, chat_id, "⏱ Генерация заняла слишком много времени. Попробуйте еще раз!")
                    
                    except Exception as e:
                        if message_id:
                            edit_message(bot_token, chat_id, message_id, "❌ Не удалось создать открытку. Попробуйте еще раз!")
                        else:
                            send_message(bot_token, chat_id, "❌ Не удалось создать открытку. Попробуйте еще раз!")
                else:
                    if message_id:
                        edit_message(bot_token, chat_id, message_id, "❌ Не удалось получить фото. Попробуйте еще раз!")
                    else:
                        send_message(bot_token, chat_id, "❌ Не удалось получить фото. Попробуйте еще раз!")
        
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

def send_message_return(token: str, chat_id: int, text: str):
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={'chat_id': chat_id, 'text': text}
    )
    return response.json()

def edit_message(token: str, chat_id: int, message_id: int, text: str):
    requests.post(
        f"https://api.telegram.org/bot{token}/editMessageText",
        json={'chat_id': chat_id, 'message_id': message_id, 'text': text}
    )

def delete_message(token: str, chat_id: int, message_id: int):
    requests.post(
        f"https://api.telegram.org/bot{token}/deleteMessage",
        json={'chat_id': chat_id, 'message_id': message_id}
    )

def send_photo(token: str, chat_id: int, photo_url: str, caption: str):
    requests.post(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        json={'chat_id': chat_id, 'photo': photo_url, 'caption': caption}
    )