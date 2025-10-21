'''
Business: Generate greeting card images using Google Gemini API
Args: event with POST body containing imageBase64; context with request_id
Returns: HTTP response with generated image URL
'''

import json
import os
import base64
import requests
from typing import Dict, Any

DEFAULT_PROMPT = """
Create an absolutely insane, over-the-top, maximalist greeting card in the style of 'Russian grandmother WhatsApp cards' or 'Eastern European tacky greeting cards'.

Your MAIN TASK: Carefully extract the main character from the provided photo (completely ignoring their background) and place them in the CENTER of this chaotic greeting card scene. The character must become an organic part of the scene, NOT just pasted in a frame. NO photo frames around the character! The effect should be eye-burning, humorous, and pushed to complete absurdity.

Study the aesthetic of such cards: it's visual cacophony where incompatible elements collide in the most garish way possible.

**MANDATORY STYLE REQUIREMENTS:**

1. **Background:** NO simple backgrounds! Use screaming, clashing gradients (acid green with hot pink, neon purple with golden yellow) OR seamless patterns of roses, daisies, or other flowers. The background must be SATURATED and AGGRESSIVE.

2. **Decorative Elements (ADD AS MANY AS POSSIBLE!):**
   * **Flowers:** MUST include bouquets or branches of red roses with unnatural glossy shine and sparkle effects
   * **Glitter and shine:** The ENTIRE image must be covered with glitter, sparkles, stars, and lens flare effects. Create the feeling that the card is glowing and shimmering from every angle
   * **Luxury symbols (inappropriately placed):** Gold pocket watches, gift baskets with cognac and chocolates, scattered dollar bills, gold coins, champagne bottles, luxury cars in the background
   * **Cute elements:** Doves, butterflies, cherubs/angels, hearts (all with excessive shine)
   * **KITTENS AND PUPPIES (MANDATORY!):** Add adorable kittens and puppies with huge sparkling eyes, fluffy fur with glow effects. They should be scattered throughout the composition, looking overly cute and unrealistic
   * **Religious symbols:** Crosses with golden glow, church domes, candles
   * **Nature overkill:** Rainbows, sunbeams, falling petals, swans

3. **Border:** NO frame around the character! Instead, add an ornate border around the ENTIRE card edges - elaborate floral patterns, golden baroque ornaments, or pearl strings.

4. **Text (CRUCIAL ELEMENT):**
   * **Font style:** Complex, handwritten, cursive, calligraphic fonts
   * **Font decoration:** Text must be BRIGHT: gold, rainbow, or gradient. MANDATORY thick outer stroke (white or contrasting color) and heavy drop shadow. Text must look 3D, embossed, and shiny
   * **LANGUAGE: ALL TEXT MUST BE IN RUSSIAN!**
   * **Content:** Choose ONE phrase from this list OR create your own in similar style:
     
     - "Счастья, здоровья, всех благ!"
     - "Благослови тебя Господь!"
     - "Пусть ангел-хранитель всегда будет рядом!"
     - "Мира и добра вашему дому!"
     - "Доброго утра! Пусть день сложится удачно!"
     - "Любви и тепла!"
     - "Поздравляю от всей души!"
     - "Пусть сбудутся все мечты!"
     - "Здоровья крепкого и счастья!"
     - "С Божьей помощью всё получится!"
     - "Радости и благополучия!"
     - "Пусть в душе всегда цветёт весна!"
     
   * Feel free to ADD MORE similar overly-sentimental phrases in Russian if it fits the composition!

5. **Overall atmosphere:** MAXIMUM KITSCH. Combination of the incompatible. Complete visual overload. The goal is to create something SO tasteless that it becomes hilarious and endearing. Think: "My eyes are bleeding but I can't look away."

**TECHNICAL DETAILS:**
- Extremely high saturation
- Multiple light sources creating chaos
- Layering of transparent elements
- Glossy, plastic-like finish on everything
- Chromatic aberration and glow effects
- More is MORE - if you think it's too much, add MORE

Make it look like it was created by someone who just discovered Photoshop's every filter and effect and decided to use ALL of them at once.
"""


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
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
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    api_key = os.environ.get('GEMINI_API_KEY')
    proxy_url = os.environ.get('HTTP_PROXY_URL')
    
    if not api_key:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'GEMINI_API_KEY not configured'})
        }
    
    body_data = json.loads(event.get('body', '{}'))
    image_base64 = body_data.get('imageBase64', '')
    
    if not image_base64:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'imageBase64 is required'})
        }
    
    if ',' in image_base64:
        image_base64 = image_base64.split(',')[1]
    
    try:
        proxies = None
        if proxy_url:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}'
        
        payload = {
            'contents': [{
                'parts': [
                    {'text': DEFAULT_PROMPT},
                    {
                        'inline_data': {
                            'mime_type': 'image/jpeg',
                            'data': image_base64
                        }
                    }
                ]
            }],
            'generationConfig': {
                'temperature': 1,
                'topK': 40,
                'topP': 0.95,
                'maxOutputTokens': 8192,
                'responseMimeType': 'image/jpeg'
            }
        }
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            proxies=proxies,
            timeout=120
        )
        
        if response.status_code != 200:
            return {
                'statusCode': response.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Gemini API error: {response.status_code}',
                    'details': response.text
                })
            }
        
        result = response.json()
        
        if 'candidates' not in result or not result['candidates']:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No image generated',
                    'details': result
                })
            }
        
        parts = result['candidates'][0].get('content', {}).get('parts', [])
        if not parts or 'inline_data' not in parts[0]:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No image data in response',
                    'details': result
                })
            }
        
        generated_image_base64 = parts[0]['inline_data']['data']
        image_data_url = f'data:image/jpeg;base64,{generated_image_base64}'
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'imageUrl': image_data_url
            })
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Request error: {str(e)}'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal error: {str(e)}'
            })
        }
