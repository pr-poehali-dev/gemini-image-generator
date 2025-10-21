'''
Business: Generate AI greeting cards using NanoBanana API
Args: event with POST body containing prompt; context with request_id
Returns: HTTP response with generated image URL
'''

import json
import os
import time
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
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
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
    
    api_key = os.environ.get('NANOBANANA_API_KEY')
    print(f"API key present: {bool(api_key)}")
    
    if not api_key:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'API key not configured'})
        }
    
    imgbb_key = os.environ.get('IMGBB_API_KEY')
    if not imgbb_key:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'ImgBB API key not configured'})
        }
    
    body_data = json.loads(event.get('body', '{}'))
    image_base64 = body_data.get('imageBase64')
    custom_prompt = body_data.get('prompt', 
        DEFAULT_PROMPT)
    
    print(f"Using prompt: {custom_prompt[:50]}...")
    print(f"Image provided: {bool(image_base64)}")
    
    image_url = None
    
    if image_base64:
        print("Uploading image to ImgBB...")
        
        image_data = image_base64.split(',')[1] if ',' in image_base64 else image_base64
        
        imgbb_response = requests.post(
            f'https://api.imgbb.com/1/upload?key={imgbb_key}',
            data={'image': image_data},
            timeout=30
        )
        
        if imgbb_response.status_code == 200:
            imgbb_result = imgbb_response.json()
            if imgbb_result.get('success'):
                image_url = imgbb_result['data']['url']
                print(f"Image uploaded successfully: {image_url}")
            else:
                print(f"ImgBB upload failed: {imgbb_result}")
        else:
            print(f"ImgBB upload error: {imgbb_response.status_code} - {imgbb_response.text}")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'prompt': custom_prompt,
        'numImages': 1,
        'type': 'TEXTTOIAMGE',
        'image_size': '1:1'
    }
    
    if image_url:
        payload['imageUrls'] = [image_url]
        print(f"Added image URL to payload: {image_url}")
    
    print(f"Sending request to NanoBanana API...")
    
    response = requests.post(
        'https://api.nanobananaapi.ai/api/v1/nanobanana/generate',
        headers=headers,
        json=payload,
        timeout=60
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text[:500]}")
    
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Generation failed',
                'details': response.text
            })
        }
    
    result = response.json()
    print(f"Parsed result: {json.dumps(result)[:500]}")
    
    if result.get('code') != 200:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'API error',
                'message': result.get('msg', 'Unknown error'),
                'details': result
            })
        }
    
    data = result.get('data', {})
    task_id = data.get('taskId')
    
    if not task_id:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'No task ID in response',
                'details': result
            })
        }
    
    print(f"Got task ID: {task_id}, polling for result...")
    
    max_attempts = 30
    poll_interval = 2
    
    for attempt in range(max_attempts):
        time.sleep(poll_interval)
        
        print(f"Polling attempt {attempt + 1}/{max_attempts}")
        
        status_response = requests.get(
            f'https://api.nanobananaapi.ai/api/v1/nanobanana/record-info?taskId={task_id}',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10
        )
        
        if status_response.status_code != 200:
            print(f"Status check failed: {status_response.status_code}")
            continue
        
        status_result = status_response.json()
        print(f"Status result: {json.dumps(status_result)[:500]}")
        
        if status_result.get('code') != 200:
            continue
        
        status_data = status_result.get('data', {})
        success_flag = status_data.get('successFlag')
        
        if success_flag == 1:
            response_data = status_data.get('response', {})
            image_url = response_data.get('resultImageUrl')
            
            if image_url:
                print(f"Generation successful! Image URL: {image_url}")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'isBase64Encoded': False,
                    'body': json.dumps({
                        'success': True,
                        'imageUrl': image_url,
                        'taskId': task_id,
                        'requestId': context.request_id
                    })
                }
        
        error_code = status_data.get('errorCode')
        if error_code and error_code != 0:
            error_message = status_data.get('errorMessage', 'Unknown error')
            print(f"Generation failed with error: {error_message}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Generation failed',
                    'message': error_message,
                    'errorCode': error_code
                })
            }
    
    return {
        'statusCode': 408,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': 'Generation timeout',
            'message': 'Image generation took too long',
            'taskId': task_id
        })
    }