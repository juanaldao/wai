import os
import logging
from flask import Flask, request, jsonify, redirect, url_for
from twilio.rest import Client
import openai

# --- App setup ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- Env vars ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # keep your existing default/model

# Configure OpenAI (legacy SDK style to match many existing repos)
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Twilio client (constructed lazily in handler so missing vars don't crash import)
def _twilio_client():
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN):
        raise RuntimeError("Missing Twilio credentials (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN)")
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- Utility: parse inbound body in both form and JSON ---
def _get_inbound_fields():
    """
    Twilio sends application/x-www-form-urlencoded by default.
    We also support JSON for manual tests.
    """
    if request.content_type and "application/json" in request.content_type.lower():
        payload = request.get_json(silent=True) or {}
        body = (payload.get("Body") or "").strip()
        from_num = payload.get("From")
        to_num = payload.get("To") or TWILIO_PHONE_NUMBER
    else:
        body = (request.form.get("Body") or "").strip()
        from_num = request.form.get("From")
        to_num = request.form.get("To") or TWILIO_PHONE_NUMBER
    return body, from_num, to_num

# --- Health check / root routes (Option B) ---
@app.get("/")
def ping():
    """Simple health endpoint so / doesn't 404."""
    return "ok", 200

@app.post("/")
def root_post():
    """
    Forward POST / to /webhook using a 307 redirect
    (preserves method and body, which Twilio follows).
    """
    return redirect(url_for("webhook"), code=307)

# --- Webhook ---
@app.route("/webhook", methods=["POST", "OPTIONS"])
def webhook():
    # Handle CORS preflight if any intermediary sends it (harmless for Twilio)
    if request.method == "OPTIONS":
        return ("", 204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        })

    app.logger.info(
        "Incoming webhook: path=%s method=%s content_type=%s",
        request.path, request.method, request.headers.get("Content-Type"),
    )

    try:
        body, from_num, to_num = _get_inbound_fields()

        if not body:
            return jsonify({"ok": False, "error": "Empty message body"}), 400
        if not TWILIO_PHONE_NUMBER:
            return jsonify({"ok": False, "error": "TWILIO_PHONE_NUMBER not configured"}), 500

        # --- Generate a reply with OpenAI (legacy ChatCompletion call, matching many existing setups) ---
        reply_text = "Thanks! 👋"  # fallback
        if OPENAI_API_KEY:
            try:
                chat = openai.ChatCompletion.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for WhatsApp messages."},
                        {"role": "user", "content": body},
                    ],
                    temperature=0.7,
                )
                reply_text = (chat["choices"][0]["message"]["content"] or "").strip() or reply_text
            except Exception as oe:
                app.logger.exception("OpenAI error: %s", oe)
                # Keep going; we can still acknowledge via Twilio

        # --- Send via Twilio REST (out-of-band reply) ---
        try:
            client = _twilio_client()
            client.messages.create(
                body=reply_text,
                from_=TWILIO_PHONE_NUMBER,
                to=from_num,
            )
        except Exception as te:
            app.logger.exception("Twilio send error: %s", te)
            return jsonify({"ok": False, "error": "Failed to send via Twilio"}), 502

        return jsonify({"ok": True})

    except Exception as e:
        app.logger.exception("Webhook handling error: %s", e)
        return jsonify({"ok": False, "error": "Unhandled server error"}), 500

# --- Local dev entrypoint (Cloud Run uses Gunicorn from Dockerfile) ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)
