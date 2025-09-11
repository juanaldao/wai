from flask import Flask, request, jsonify
from twilio.rest import Client  # Add Twilio REST client for sending messages
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os

app = Flask(__name__)

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")  # New Twilio variables
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(twilio_account_sid, twilio_auth_token)  # Initialize Twilio client

@app.route("/webhook", methods=["POST"])
def webhook():
    # Get the incoming message
    incoming_msg = request.form.get("Body")
    sender = request.form.get("From")

    # Generate a response using OpenAI GPT-4
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": incoming_msg}
            ]
        )
        reply = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        reply = "Sorry, I couldn't process your request. Please try again later."

    # Send a reply back using Twilio
    client.messages.create(
        from_=twilio_phone_number,
        to=sender,
        body=reply
    )

    return jsonify({"status": "success", "message": "Message sent."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))