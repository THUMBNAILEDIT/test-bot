from flask import Flask, request, jsonify, render_template
from webhooks import handler, asana_webhook
from commands import app
from slack_bolt.adapter.flask import SlackRequestHandler
from purchase_handler import handle_purchase, verify_access_token

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    try:
        return handler.handle(request)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Invalid request format", "message": str(e)}), 400

@flask_app.route("/slack/commands", methods=["POST"])
def slack_commands():
    return handler.handle(request)

@flask_app.route("/asana-webhook", methods=["POST"])
def asana_webhook_route():
    return asana_webhook()

@flask_app.route("/pricing/<access_token>")
def pricing_page(access_token):
    logger.info(f"Received AccessToken: {access_token}")
    response = verify_access_token(access_token)
    if response[1] != 200:
        return render_template("403.html"), 403

    return render_template("pricing.html", access_token=access_token)

@flask_app.route("/api/purchase", methods=["POST"])
def purchase():
    return handle_purchase(request.json)

if __name__ == "__main__":
    flask_app.run(debug=True, host="0.0.0.0", port=5000)