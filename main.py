from flask import Flask, request, jsonify
from webhooks import handler, asana_webhook
from commands import app
from slack_bolt.adapter.flask import SlackRequestHandler

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

if __name__ == "__main__":
    flask_app.run(debug=True, host="0.0.0.0", port=5000)