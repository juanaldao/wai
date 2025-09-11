from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os

app = Flask(__name__)

# Load OpenAI API Key (set this as an environment variable in Cloud Run)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/webhook", methods=["POST"])
def webhook():
    # Get the incoming message
    incoming_msg = request.form.get("Body")
    sender = request.form.get("From")

    # Generate a response using OpenAI GPT-4
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use GPT-4 model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": incoming_msg}
            ]
        )
        reply = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        reply = "Sorry, I couldn't process your request. Please try again later."

    # Create Twilio MessagingResponse
    twilio_response = MessagingResponse()
    twilio_response.message(reply)

    return str(twilio_response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))