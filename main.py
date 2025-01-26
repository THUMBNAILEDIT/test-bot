# from flask import Flask, request, jsonify, render_template
# from webhooks import handler, asana_webhook
# from commands import app
# from slack_bolt.adapter.flask import SlackRequestHandler
# from purchase_handler import send_invoice_to_monobank, process_payment_webhook, handle_purchase, verify_access_token

# import logging

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# flask_app = Flask(__name__)
# handler = SlackRequestHandler(app)

# @flask_app.route("/slack/events", methods=["POST"])
# def slack_events():
#     try:
#         return handler.handle(request)
#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"error": "Invalid request format", "message": str(e)}), 400

# @flask_app.route("/slack/commands", methods=["POST"])
# def slack_commands():
#     return handler.handle(request)

# @flask_app.route("/asana-webhook", methods=["POST"])
# def asana_webhook_route():
#     return asana_webhook()

# @flask_app.route("/pricing/<access_token>")
# def pricing_page(access_token):
#     logger.info(f"Received AccessToken: {access_token}")
#     response = verify_access_token(access_token)
#     if response[1] != 200:
#         return render_template("403.html"), 403

#     return render_template("pricing.html", access_token=access_token)

# # @flask_app.route("/api/purchase", methods=["POST"])
# # def purchase():
# #     return handle_purchase(request.json)

# @flask_app.route("/api/create-invoice", methods=["POST"])
# def create_invoice():
#     data = request.get_json()
#     total = data.get("total")
#     access_token = data.get("access_token")

#     if not total or not access_token:
#         return jsonify({"error": "Total and AccessToken are required"}), 400

#     response, status_code = send_invoice_to_monobank(total, access_token)
#     return jsonify(response), status_code

# @flask_app.route("/monobank/webhook/payment", methods=["POST"])
# def handle_payment_webhook():
#     data = request.get_json()
#     return process_payment_webhook(data)

# if __name__ == "__main__":
#     flask_app.run(debug=True, host="0.0.0.0", port=5000)

# ===============================

# from flask import Flask, request, jsonify, render_template
# from webhooks import handler, asana_webhook
# from commands import app
# from slack_bolt.adapter.flask import SlackRequestHandler
# from purchase_handler import send_invoice_to_monobank, process_monobank_payment_webhook, verify_access_token
# from logger import logger

# flask_app = Flask(__name__)
# handler = SlackRequestHandler(app)

# @flask_app.route("/slack/events", methods=["POST"])
# def slack_events():
#     try:
#         return handler.handle(request)
#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"error": "Invalid request format", "message": str(e)}), 400

# @flask_app.route("/slack/commands", methods=["POST"])
# def slack_commands():
#     return handler.handle(request)

# @flask_app.route("/asana-webhook", methods=["POST"])
# def asana_webhook_route():
#     return asana_webhook()

# @flask_app.route("/pricing/<access_token>")
# def pricing_page(access_token):
#     logger.info(f"Received AccessToken: {access_token}")
#     response = verify_access_token(access_token)
#     if response[1] != 200:
#         return render_template("403.html"), 403

#     return render_template("pricing.html", access_token=access_token)

# @flask_app.route("/api/create-invoice", methods=["POST"])
# def create_invoice():
#     data = request.get_json()
#     logger.info(f"Received data for invoice creation: {data}")
#     total = data.get("total")
#     access_token = data.get("access_token")

#     if not total or not access_token:
#         logger.error("Total and AccessToken are required but not provided")
#         return jsonify({"error": "Total and AccessToken are required"}), 400

#     response, status_code = send_invoice_to_monobank(total, access_token)
#     logger.info(f"Response from send_invoice_to_monobank: {response}, Status code: {status_code}")
#     return jsonify(response), status_code

# @flask_app.route("/monobank/webhook", methods=["POST"])
# def monobank_webhook():
#     data = request.get_json()
#     logger.info(f"Received webhook data from Monobank: {data}")
#     return process_monobank_payment_webhook(data)

# if __name__ == "__main__":
#     flask_app.run(debug=True, host="0.0.0.0", port=5000)

from flask import Flask, request, jsonify, render_template
from webhooks import handler, asana_webhook
from commands import app
from slack_bolt.adapter.flask import SlackRequestHandler
from purchase_handler import send_invoice_to_monobank, process_monobank_payment_webhook, verify_access_token
from slack_oauth import handle_oauth_callback
from logger import logger
import requests

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    try:
        return handler.handle(request)
    except Exception as e:
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

@flask_app.route("/api/create-invoice", methods=["POST"])
def create_invoice():
    data = request.get_json()
    logger.info(f"Received data for invoice creation: {data}")
    total = data.get("total")
    access_token = data.get("access_token")

    if not total or not access_token:
        logger.error("Total and AccessToken are required but not provided")
        return jsonify({"error": "Total and AccessToken are required"}), 400

    response, status_code = send_invoice_to_monobank(total, access_token)
    logger.info(f"Response from send_invoice_to_monobank: {response}, Status code: {status_code}")
    return jsonify(response), status_code

@flask_app.route("/monobank/webhook", methods=["POST"])
def monobank_webhook():
    data = request.get_json()
    logger.info(f"Received webhook data from Monobank: {data}")
    return process_monobank_payment_webhook(data)

@flask_app.route("/slack/oauth/callback", methods=["GET"])
def oauth_callback():
    return handle_oauth_callback()

if __name__ == "__main__":
    flask_app.run(debug=True, host="0.0.0.0", port=5000)