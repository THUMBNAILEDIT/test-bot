import logging
from flask import Flask, request, jsonify, render_template, make_response
from payment.validate_webhook_request import validate_request
from communication.webhooks import handler, asana_webhook
from communication.commands import app
from slack_bolt.adapter.flask import SlackRequestHandler
from payment.purchase_handler import process_monobank_payment_webhook, verify_access_token, send_invoice_to_monobank, send_invoice_to_monobank_landing, process_monobank_payment_webhook_landing
from database.database import supabase, complete_client_profile
from flask_cors import CORS, cross_origin

# ========================================================

flask_app = Flask(__name__, template_folder="payment/templates", static_folder="payment/static")
# CORS(flask_app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
CORS(flask_app)
handler = SlackRequestHandler(app)

# ========================================================

@flask_app.route("/slack/events", methods=["GET", "POST"])
def slack_events():
    try:
        if request.method == "GET":
            # logging.info("GET request received at /slack/events")
            return "Endpoint verified", 200

        if request.method == "POST":
            return handler.handle(request)

    except Exception as e:
        logging.error(f"Error: {e}")

        return jsonify({"error": "Invalid request format", "message": str(e)}), 400

# ========================================================

@flask_app.route("/slack/commands", methods=["POST"])
def slack_commands():
    return handler.handle(request)

# ========================================================

@flask_app.route("/asana-webhook", methods=["POST"])
def asana_webhook_route():
    return asana_webhook()

# ========================================================

@flask_app.route("/pricing/<access_token>")
def pricing_page(access_token):

    response = verify_access_token(access_token)
    if response[1] != 200:
        return render_template("403.html"), 403

    client_data = supabase.table("clientbase").select("is_subscription_active").eq("access_token", access_token).execute()
    
    is_subscription_active = client_data.data[0]["is_subscription_active"] if client_data.data else "hello"

    return render_template("pricing.html", access_token=access_token, is_subscription_active="true" if is_subscription_active else "false")

# ========================================================

@flask_app.route("/api/create-invoice", methods=["POST"])
def create_invoice():
    data = request.get_json()
    total = data.get("total")
    access_token = data.get("access_token")

    if not total or not access_token:
        return jsonify({"error": "Total and AccessToken are required"}), 400

    response, status_code = send_invoice_to_monobank(total, access_token)
    return jsonify(response), status_code

# ========================================================

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

# ======================================================== LANDING

@flask_app.route("/api/create-invoice-landing", methods=["POST", "OPTIONS"])
@cross_origin()
def create_invoice_landing():
    if request.method == "OPTIONS":
        return '', 200

    data = request.get_json()
    total = data.get("total")
    reference = data.get("reference")

    if not total or not reference:
        return jsonify({"error": "Total and reference are required"}), 400

    response, status_code = send_invoice_to_monobank_landing(total, reference)
    return jsonify(response), status_code

# =============================================================

@flask_app.route("/monobank/webhook-landing", methods=["POST", "OPTIONS"])
@cross_origin()
def monobank_webhook_landing():
    if request.method == "OPTIONS":
        return '', 200

    x_sign_base64 = request.headers.get('X-Sign')
    body_bytes = request.get_data()
    body = request.get_json()

    if not x_sign_base64 or not body_bytes:
        return jsonify({"error": "Missing signature or body"}), 400

    if validate_request(x_sign_base64, body_bytes):
        return process_monobank_payment_webhook_landing(body)
    else:
        return jsonify({"error": "Invalid signature"}), 400
    
# =============================================================

@flask_app.route("/api/access-token-from-reference")
def access_token_from_reference():
    reference = request.args.get("reference")
    if not reference:
        return jsonify({"error": "Missing reference"}), 400

    result = supabase.table("clientbase").select("access_token").eq("reference", reference).execute()
    if result.data:
        return jsonify({"access_token": result.data[0]["access_token"]}), 200
    return jsonify({"error": "Access token not found"}), 404
    
@flask_app.route("/complete-profile/<access_token>")
def complete_profile_page(access_token):
    return render_template("complete-profile.html", access_token=access_token)

# =============================================================

@flask_app.route("/api/complete-profile", methods=["POST"])
def complete_profile():
    data = request.get_json()
    access_token = data.get("access_token")

    if not access_token:
        return jsonify({"error": "Missing access token"}), 400

    success = complete_client_profile(access_token, data)

    if success:
        return jsonify({"message": "Profile updated"}), 200
    else:
        return jsonify({"error": "No valid fields to update"}), 400
    
# =============================================================

@flask_app.route("/post-payment")
def post_payment():
    return render_template("post_payment.html")

# =============================================================

if __name__ == "__main__":
    flask_app.run(debug=True, host="0.0.0.0", port=5000)