import os
import requests
from dotenv import load_dotenv

load_dotenv()

INFERMEDICA_APP_ID = os.environ.get("INFERMEDICA_APP_ID")
INFERMEDICA_APP_KEY = os.environ.get("INFERMEDICA_APP_KEY")

HEADERS = {
    "App-Id": INFERMEDICA_APP_ID,
    "App-Key": INFERMEDICA_APP_KEY,
    "Content-Type": "application/json"
}

# Symptoms endpoint requires age and sex parameters
params = {
    "age.value": 35,
    "sex": "male"
}

response = requests.get(
    "https://api.infermedica.com/v3/symptoms",
    headers=HEADERS,
    params=params
)

print(f"Status code: {response.status_code}")
data = response.json()

if response.status_code == 200:
    print(f"Total symptoms: {len(data)}\n")
    
    search_terms = [
        "headache", "dizziness", "nausea", "chest",
        "pain", "fever", "cough", "stomach", "abdominal",
        "vomit", "throat", "fatigue", "weakness"
    ]
    
    for term in search_terms:
        matches = [s for s in data if term.lower() in s['name'].lower()][:3]
        if matches:
            for m in matches:
                print(f"{term}: {m['id']} — {m['name']}")
        else:
            print(f"{term}: NO MATCH")
        print()
else:
    print(f"Error: {response.text}")