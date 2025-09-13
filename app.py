from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/reply_whatsapp", methods=['POST'])
def reply_whatsapp():
    resp = MessagingResponse()
    resp.message("Qué te pasa flaco?.")
    return Response(str(resp), mimetype='text/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
