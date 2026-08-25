import os
import requests

api_key = None
model_name = "gemini-3.5-flash-lite" # fallback

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('GEMINI_API_KEY='):
            api_key = line.strip().split('=', 1)[1]
        elif line.startswith('GEMINI_MODEL='):
            model_name = line.strip().split('=', 1)[1]

if not api_key:
    print("API Key not found in .env")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
headers = {'Content-Type': 'application/json'}
data = {
    "contents": [{"parts":[{"text": "Hello, this is a test. Reply with 'Working'."}]}]
}
print(f"Testing API key ending in ...{api_key[-4:]} with model {model_name}")
response = requests.post(url, headers=headers, json=data)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("Success! Response from Gemini:")
    print(response.json()['candidates'][0]['content']['parts'][0]['text'])
else:
    print("Failed. Error details:")
    print(response.text)
