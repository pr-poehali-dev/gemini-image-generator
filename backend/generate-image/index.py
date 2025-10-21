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