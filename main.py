import os

import openai
from pydantic import BaseModel

from fastapi import FastAPI

# Set up the OpenAI API key (store it in your environment variables)
openai.api_key = os.getenv("OPENAI_API_KEY")
OMNISEND_API_KEY = os.getenv("OMNISEND_API_KEY")

app = FastAPI()


# Define a Pydantic model for the webhook input
class WhiskyData(BaseModel):
    email: str
    whisky_preferences: list


# Endpoint to handle the form data and generate whisky recommendations
@app.post("/recommendation")
async def create_recommendation(data: WhiskyData):
    # Prepare the message for ChatGPT
    whisky_list = ", ".join(
        data.whisky_preferences
    )  # Convert list to a comma-separated string
    messages = [
        {
            "role": "system",
            "content": "You are a whisky expert speaking directly to the customer, analyzing their preferences and giving recommendations.",
        },
        {
            "role": "user",
            "content": f"Based on your top 3 whisky rankings, in order: {whisky_list}, here's your whisky profile. Then, based on that profile, here are five other whiskies you should try.",
        },
    ]

    # Send the message to ChatGPT and get the response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Use the correct chat model
            messages=messages,
            max_tokens=500,  # Adjust tokens based on how much text you need
            temperature=0.7,
        )
        recommendations = response["choices"][0]["message"][
            "content"
        ].strip()  # Extract the recommendation text

        import requests

        response = requests.patch(
            url=f"https://api.omnisend.com/v5/contacts?email={data.email}",
            headers={
                "X-API-KEY": f"{OMNISEND_API_KEY}",
                "accept": "application/json",
                "content-type": "application/json",
            },
            json={"state": f"{recommendations}"},
        )

        # print(response.status_code)
        # print(response.json())

        return {"status": data.email, "recommendations": recommendations}
    except Exception as e:
        return {"error": str(e)}
