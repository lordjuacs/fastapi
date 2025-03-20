from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os
import requests

# Set up the OpenAI API key (store it in your environment variables)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Omnisend API Key (also store this securely in environment variables)
OMNISEND_API_KEY = os.getenv("OMNISEND_API_KEY")

app = FastAPI()

# Define a Pydantic model for the webhook input
class WhiskyData(BaseModel):
    email: str
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
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code in [200, 201]:
        print("Successfully updated Omnisend contact.")
    else:
        print(f"Failed to update Omnisend contact: {response.status_code} - {response.text}")

# Endpoint to handle the form data and generate whisky recommendations
@app.post("/recommendation")
async def create_recommendation(data: WhiskyData):
    # Prepare the message for ChatGPT
    whisky_list = ", ".join(data.whisky_preferences)
    messages = [
        {"role": "system", "content": "You are a whisky expert helping users discover new whiskies."},
        {"role": "user", "content": f"Based on these top 3 whiskies: {whisky_list}, give me 5 other whisky recommendations."}
    ]

    # Send the message to ChatGPT and get the response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        recommendations = response["choices"][0]["message"]["content"].strip()

        # Store recommendation back into Omnisend immediately after generation
        update_omnisend_contact(data.email, recommendations)

        return {"email": data.email, "recommendations": recommendations}

    except Exception as e:
        return {"error": str(e)}
