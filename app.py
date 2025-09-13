from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import os
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt4(question: str) -> str:
    """
    Ask a question to GPT-4 and return the response text.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # use "gpt-4o-mini" (faster/cheaper) or "gpt-4"
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route("/reply_whatsapp", methods=['POST'])
def reply_whatsapp():
    incoming_msg = request.form.get("Body", "").strip()
    gpt4_response = ask_gpt4(incoming_msg)
    resp = MessagingResponse()
    resp.message(gpt4_response)
    return Response(str(resp), mimetype='text/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
