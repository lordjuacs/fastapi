from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
import os
from openai import OpenAI
import requests
from datetime import datetime

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OMNISEND_API_KEY = os.getenv("OMNISEND_API_KEY")

app = FastAPI()

# Define a Pydantic model for the webhook input
class WhiskyData(BaseModel):
    email: EmailStr  # Validate email format
    whisky_preferences: list

# Function to update Omnisend contact with recommendation
def update_omnisend_contact(email: str, recommendation: str):
    url = "https://api.omnisend.com/v3/contacts"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": OMNISEND_API_KEY
    }
    data = {
        "email": email,
        "fields": {
            "whisky_recommendation": recommendation
        },
        "status": "subscribed",
        "statusDate": datetime.utcnow().isoformat() + "+00:00"
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code in [200, 201]:
            print("Successfully updated Omnisend contact.")
        else:
            print(f"Failed to update Omnisend contact: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error while updating Omnisend contact: {str(e)}")

# Endpoint to handle the form data and generate whisky recommendations
@app.post("/recommendation")
async def create_recommendation(data: WhiskyData):
    print(f"Received data: {data}")  # Debug incoming data

    # Prepare the message for ChatGPT
    whisky_list = ", ".join(data.whisky_preferences)
    messages = [
        {"role": "system", "content": "You are a whisky expert helping users discover new whiskies."},
        {"role": "user", "content": f"Based on these top 3 whiskies: {whisky_list}, give me 5 other whisky recommendations."}
    ]

    # Send the message to ChatGPT and get the response
    try:
        recommendation = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        ).choices[0].message["content"].strip()

        # Store recommendation back into Omnisend immediately after generation
        update_omnisend_contact(data.email, recommendation)

        return {"email": data.email, "recommendations": recommendation}

    except Exception as e:
        return {"error": str(e)}
