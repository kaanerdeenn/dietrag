import sys
sys.path.append("C:\\Users\\kaan\\Desktop\\diyet-rag")

import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

response = client.post("/chat", json={
    "user_id": 1,
    "user_message": "Sabahki kahvaltımdan sonra öğlen ne yemeliyim?",
    "history": "",
    "boy_cm": 180,
    "kilo_kg": 75,
    "yas": 25,
    "cinsiyet": "erkek",
    "bugunku_ogunler": [
        {
            "food_name": "karpuz",
            "calories": 500,
            "protein": 0,
            "fat": 0,
            "carbs": 0
        }
    ]
})

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
