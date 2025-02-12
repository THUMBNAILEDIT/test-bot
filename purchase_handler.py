from flask import jsonify

from config import MONOBANK_API_BASEURL, BACKEND_BASEURL, MONOBANK_API_KEY
from database import supabase
import requests
import datetime
import pytz

from payment.payment_plan import calculate_credits_with_workaround, get_plan_from_total, PricingPlans


def verify_access_token(access_token):
    if not access_token:
        return {"error": "AccessToken is required"}, 403

    response = supabase.table("clientbase").select("*").eq("access_token", access_token).execute()
    if not response.data:
        return {"error": f"AccessToken '{access_token}' not found"}, 403

    return {"message": "AccessToken is valid"}, 200

def send_invoice_to_monobank(total, access_token):
    try:
        monobank_payload = {
            "amount": int(total * 100),
            "ccy": 840,
            "merchantPaymInfo": {
                "comment": "Service Purchase",
                "destination": f"{total}",
                "reference": access_token
            },
            "webHookUrl": BACKEND_BASEURL+"monobank/webhook",
            "saveCardData": {
                "saveCard": True,
            },
        }
        headers = {"X-Token": MONOBANK_API_KEY }
        response = requests.post(MONOBANK_API_BASEURL+"merchant/invoice/create", json=monobank_payload, headers=headers)
        if response.status_code == 200:
            monobank_data = response.json()
            return {"payment_url": monobank_data.get("pageUrl")}, 200
        else:
            return {"error": "Failed to create invoice", "details": response.json()}, response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def calculate_credits(plan, total):
    if plan == "monthly":
        pricing_table = {
            240: 4, 456: 8, 648: 12, 816: 16, 960: 20,
            1080: 24, 1092: 28, 1248: 32, 1440: 40,
            1728: 48, 2016: 56, 1296: 36, 2592: 72, 3024: 84
        }
        return pricing_table.get(total, 0)
    elif plan == "annual":
        pricing_table = {
            2594: 4, 4925: 8, 6998: 12, 8813: 16, 10368: 20,
            11664: 24, 12701: 28, 13478: 32, 15552: 40,
            18662: 48, 21773: 56, 13997: 36, 23328: 60, 27994: 72, 32659: 84
        }
        return pricing_table.get(total, 0)
    elif plan == "onetime":
        pricing_table = {
            70: 1, 140: 2, 210: 3, 260: 4, 325: 5,
            390: 6, 455: 7, 480: 8, 540: 9, 600: 10,
        }
        return pricing_table.get(total, 0)
    else:
        return 0

def process_payment(data):
    try:
        payment_status = data.get("status")
        access_token = data.get("reference")
        total = data.get("amount")
        plan = data.get("plan")

        if not access_token or not total:
            return jsonify({"error": "Invalid webhook data"}), 400

        if payment_status == "success":
            response = supabase.table("clientbase").select("current_credits").eq("access_token", access_token).execute()
            if response.data:
                client = response.data[0]
                current_credits = client.get("current_credits", 0)
                new_credits = current_credits + calculate_credits(plan, total)
                supabase.table("clientbase").update({"current_credits": new_credits}).eq("access_token", access_token).execute()
                return jsonify({"message": "Credits updated successfully"}), 200

        return jsonify({"error": "Payment not successful or invalid status"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def load_card_token(invoice_id):
    try:
        response = requests.get(f"https://api.monobank.ua/api/merchant/invoice/status?invoiceId={invoice_id}", headers={"X-Token": MONOBANK_API_KEY})
        card_token = response.json().get("walletData").get("cardToken", None)
        if card_token:
            return card_token
        else:
            print("No card token found, json response:", response.json())
            return None
    except Exception as e:
        print("Error loading card token")
        return None


def update_payment_info(data):
    total = int(data.get("destination"))
    access_token = data.get("reference")
    invoice_id = data.get("invoiceId")

    card_token = load_card_token(invoice_id)
    payment_plan = get_plan_from_total(total)
    subscription_period = 30 if payment_plan == PricingPlans.Monthly else 365 if payment_plan == PricingPlans.Annual else None

    utc_timezone = pytz.utc
    current_time = datetime.datetime.now(tz=utc_timezone)
    iso_time_str = current_time.isoformat()

    if subscription_period:
        new_payment_info = {
           "subscription_amount": total,
           "subscription_period": subscription_period,
           "last_subscription_transaction":iso_time_str,

       } | ({"card_token": card_token} if card_token else {})

        (supabase.table("clientbase")
         .update(new_payment_info)
         .eq("access_token", access_token).execute())

def process_monobank_payment_webhook(data):
    try:
        payment_status = data.get("status")
        access_token = data.get("reference")
        # total = data.get("amount") // The best way
        total = int(data.get("destination")) if data.get("destination").isdigit() else None # But i add some shetty code like workaround for fast and easily understand))
        # plan = data.get("plan")

        if not access_token or not total:
            return {"error": "Invalid webhook data"}, 400

        if payment_status == "success":
            response = supabase.table("clientbase").select("current_credits").eq("access_token", access_token).execute()
            if response.data:
                client = response.data[0]
                current_credits = client.get("current_credits", 0)
                new_credits = current_credits + calculate_credits_with_workaround(total)
                supabase.table("clientbase").update({"current_credits": new_credits}).eq("access_token", access_token).execute()

                update_payment_info(data)

                return {"message": "Credits updated successfully"}, 200

        return {"error": "Payment not successful or invalid status"}, 400
    except Exception as e:
        return {"error": str(e)}, 500