from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os
import requests
from datetime import datetime

# Load environment variables for API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
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
        },
        "status": "subscribed",  # Mandatory field for Omnisend contact creation/update
        "statusDate": datetime.utcnow().isoformat() + "+00:00"  # Current timestamp in ISO format
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
    # Prepare the message for ChatGPT
    whisky_list = ", ".join(data.whisky_preferences)  # Convert list to a comma-separated string
    messages = [
        {"role": "system", "content": "You are a whisky expert helping users discover new whiskies."},
        {"role": "user", "content": f"Based on these top 3 whiskies: {whisky_list}, give me 5 other whisky recommendations."}
    ]

    # Send the message to ChatGPT and get the response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        recommendations = response["choices"][0]["message"]["content"].strip()  # Extract the recommendation text

        # Store recommendation back into Omnisend immediately after generation
        update_omnisend_contact(data.email, recommendations)

        return {"email": data.email, "recommendations": recommendations}

    except Exception as e:
        return {"error": str(e)}
