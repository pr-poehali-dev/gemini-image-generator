'''
Business: Generate AI-styled greeting cards using Google Gemini 2.5 Flash Image API
Args: event with POST body containing imageBase64; context with request_id
Returns: HTTP response with generated image in base64 format
'''

import json
import base64
import os
from typing import Dict, Any
from google import genai
from google.genai import types


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
    
    api_key = os.environ.get('GEMINI_API_KEY')
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
    image_base64 = body_data.get('imageBase64')
    
    if not image_base64:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Image is required'})
        }
    
    client = genai.Client(api_key=api_key)
    
    custom_prompt = """Transform this image into a vintage-style greeting card with warm, nostalgic colors. 
Add a soft glow effect and make it look like a classic handmade postcard from the 1960s. 
Keep the main subject but enhance it with artistic flourishes and decorative elements in a retro style."""
    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=custom_prompt),
            ],
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )
    
    generated_images = []
    generated_text = ""
    
    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        
        part = chunk.candidates[0].content.parts[0]
        
        if part.inline_data and part.inline_data.data:
            inline_data = part.inline_data
            image_data = base64.b64encode(inline_data.data).decode('utf-8')
            mime_type = inline_data.mime_type
            generated_images.append({
                'data': f'data:{mime_type};base64,{image_data}',
                'mimeType': mime_type
            })
        else:
            if hasattr(chunk, 'text'):
                generated_text += chunk.text
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'isBase64Encoded': False,
        'body': json.dumps({
            'success': True,
            'images': generated_images,
            'text': generated_text,
            'requestId': context.request_id
        })
    }
