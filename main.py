from flask import Flask, request, jsonify, render_template

from payment.validate_webhook_request import validate_request
from webhooks import handler, asana_webhook
from commands import app
from slack_bolt.adapter.flask import SlackRequestHandler
from purchase_handler import process_monobank_payment_webhook, verify_access_token, send_invoice_to_monobank
from database import supabase

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["GET", "POST"])
def slack_events():
    try:
        if request.method == "GET":
            print("GET request received at /slack/events")
            return "Endpoint verified", 200

        if request.method == "POST":
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

# ===

# @flask_app.route("/pricing/<access_token>")
# def pricing_page(access_token):
#     response = verify_access_token(access_token)
#     if response[1] != 200:
#         return render_template("403.html"), 403

#     return render_template("pricing.html", access_token=access_token)

# ===

# @flask_app.route("/pricing/<access_token>")
# def pricing_page(access_token):
#     response = verify_access_token(access_token)
#     if response[1] != 200:
#         return render_template("403.html"), 403

#     client_data = supabase.table("clientbase").select("is_subscription_active").eq("access_token", access_token).execute()
    
#     # is_subscription_active = client_data.data[0]["is_subscription_active"] if client_data.data else False
#     is_subscription_active = client_data.data[0]["is_subscription_active"] if client_data.data else "hello"

#     import logging
#     logging.basicConfig(level=logging.INFO)
#     logging.info(f"is_subscription_active: {is_subscription_active}")
#     logging.info(client_data)
#     logging.info(client_data.data[0])

#     return render_template("pricing.html", access_token=access_token, is_subscription_active=is_subscription_active)

@flask_app.route("/pricing/<access_token>")
def pricing_page(access_token):
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info(f"pricing_page endpoint hit with access_token: {access_token}")

    response = verify_access_token(access_token)
    if response[1] != 200:
        return render_template("403.html"), 403

    client_data = supabase.table("clientbase").select("is_subscription_active").eq("access_token", access_token).execute()
    
    is_subscription_active = client_data.data[0]["is_subscription_active"] if client_data.data else "hello"

    logging.info(f"is_subscription_active: {is_subscription_active}")

    logging.info(f"Raw client data: {client_data}")
    logging.info(f"First entry in data: {client_data.data[0] if client_data.data else 'No data'}")

    return render_template("pricing.html", 
                       access_token=access_token, 
                       is_subscription_active="true" if is_subscription_active else "false")

# ===

@flask_app.route("/api/create-invoice", methods=["POST"])
def create_invoice():
    data = request.get_json()
    total = data.get("total")
    access_token = data.get("access_token")

    if not total or not access_token:
        return jsonify({"error": "Total and AccessToken are required"}), 400

    response, status_code = send_invoice_to_monobank(total, access_token)
    return jsonify(response), status_code

@flask_app.route("/monobank/webhook", methods=["POST", "GET"])
def monobank_webhook():
    x_sign_base64 = request.headers.get('X-Sign')
    body_bytes = request.get_data()
    body = request.get_json()

    if not x_sign_base64 or not body_bytes:
        return jsonify({"error": "Missing X-Sign header or body"}), 400

    try:
        if validate_request(x_sign_base64, body_bytes):
            process_monobank_payment_webhook(body)
            return jsonify({"status": "OK"}), 200
        else:
            return jsonify({"status": "NOT OK"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    flask_app.run(debug=True, host="0.0.0.0", port=5000)