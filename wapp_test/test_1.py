import requests
import pprint
import json

url = "https://7105.api.greenapi.com/waInstance7105242930/getChatHistory/"

payload = {
    "chatId": "77006458263@c.us", 
    "count": 10
}
headers = {
    'Content-Type': 'application/json'
}

response = requests.post(url, json=payload)

# Parse the JSON response
data = response.json()

# Pretty print the parsed JSON with proper indentation
pprint.pprint(data, indent=2, width=100, sort_dicts=False)

# Save the JSON response to a file
with open('response.json', 'w') as f:
    json.dump(data, f, indent=2)

print("JSON response saved to response.json")
