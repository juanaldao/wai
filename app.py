from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import os
import openai

app = Flask(__name__)

# Set your OpenAI API key as an environment variable or directly
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_gpt4(question: str) -> str:
    """
    Ask a question to GPT-4 and return the response text.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",   # Use the appropriate GPT-4 model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            temperature=0.7  # Controls randomness (0 = deterministic, 1 = creative)
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route("/reply_whatsapp", methods=['POST'])
def reply_whatsapp():
    # Extract user's message from the incoming request
    incoming_msg = request.form.get("Body", "").strip()

    # Get GPT-4's response
    gpt4_response = ask_gpt4(incoming_msg)

    # Create Twilio's response
    resp = MessagingResponse()
    resp.message(gpt4_response)

    return Response(str(resp), mimetype='text/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
