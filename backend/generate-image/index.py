'''
Business: Generate AI greeting cards using NanoBanana API
Args: event with POST body containing prompt; context with request_id
Returns: HTTP response with generated image URL
'''

import json
import os
import requests
from typing import Dict, Any


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
    
    body_data = json.loads(event.get('body', '{}'))
    custom_prompt = body_data.get('prompt', 
        'A vintage-style greeting card with warm, nostalgic colors and soft glow effect')
    
    print(f"Using prompt: {custom_prompt[:50]}...")
    
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
    response_data = data.get('response', {})
    image_url = response_data.get('resultImageUrl')
    
    if not image_url:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'No image URL in response',
                'details': result
            })
        }
    
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
            'taskId': data.get('taskId'),
            'requestId': context.request_id
        })
    }