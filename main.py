from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os

# Set up the OpenAI API key (store it in your environment variables)
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Define a Pydantic model for the webhook input
class WhiskyData(BaseModel):
    email: str
    whisky_preferences: list

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
            model="gpt-4o-mini",  # Use the correct chat model
            messages=messages,
            max_tokens=500,  # Adjust tokens based on how much text you need
            temperature=0.7,
        )
        recommendations = response["choices"][0]["message"]["content"].strip()  # Extract the recommendation text
        return {"email": data.email, "recommendations": recommendations}
    except Exception as e:
        return {"error": str(e)}
