#!/usr/bin/env python3
import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("ZAI_CODING_API_KEY")
if not api_key:
    print("Error: ZAI_CODING_API_KEY not found")
    exit(1)

# Test different endpoint variations
endpoints = [
    "https://api.z.ai/api/coding/paas/v4/messages",
    "https://api.z.ai/coding/paas/v4/messages", 
    "https://api.z.ai/v4/messages",
    "https://api.z.ai/api/v4/messages",
]

headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

payload = {
    "model": "GLM-4.7",
    "max_tokens": 50,
    "messages": [{"role": "user", "content": "hi"}]
}

print("Testing different endpoint variations...\n")

for url in endpoints:
    print(f"Testing: {url}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ SUCCESS! This endpoint works!")
            print(f"  Response: {response.text[:200]}...")
            break
        else:
            print(f"  Response: {response.text[:200]}...")
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
    print()

print("\n" + "="*60)
print("If none worked, you may need to use the proxy approach.")
print("Start mitmproxy with: mitmproxy -s z_ai_coding_passthrough.py")
print("Then use: http://localhost:8080/api/anthropic/v1/messages")
