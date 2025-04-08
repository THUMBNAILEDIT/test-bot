import requests
import datetime
import pytz
import logging
from config.config import MONOBANK_API_BASEURL, BACKEND_BASEURL, MONOBANK_API_KEY
from communication.commands import app as slack_app
from database.database import supabase, activate_client_subscription

# ========================================================

monthly_pricing_table = {
    100: 2, 148: 3, 194: 4, 239: 5, 283: 6, 325: 7, 366: 8, 405: 9,
    443: 10, 479: 11, 514: 12, 548: 13, 580: 14, 611: 15, 640: 16, 668: 17,
    694: 18, 719: 19, 743: 20, 765: 21, 786: 22, 805: 23, 823: 24, 839: 25,
    854: 26, 868: 27, 880: 28, 892: 29, 900: 30, 930: 31, 960: 32, 990: 33,
    1020: 34, 1050: 35, 1080: 36, 1110: 37, 1140: 38, 1170: 39, 1200: 40, 1230: 41,
    1260: 42, 1290: 43, 1320: 44, 1350: 45, 1380: 46, 1410: 47, 1440: 48, 1470: 49,
    1500: 50, 1530: 51, 1560: 52, 1590: 53, 1620: 54, 1650: 55, 1680: 56, 1710: 57,
    1740: 58, 1770: 59, 1800: 60, 1860: 62, 1890: 63, 1920: 64, 1980: 66, 2040: 68,
    2070: 69, 2100: 70, 2160: 72, 2220: 74, 2250: 75, 2280: 76, 2340: 78, 2400: 80,
    2430: 81, 2460: 82, 2520: 84, 2580: 86, 2610: 87, 2640: 88, 2700: 90, 2760: 92,
    2790: 93, 2820: 94, 2880: 96, 2940: 98, 2970: 99, 3000: 100, 3060: 102, 3120: 104,
    3150: 105, 3180: 106, 3240: 108, 3300: 110, 3330: 111, 3360: 112, 3420: 114, 3480: 116,
    3510: 117, 3540: 118, 3600: 120, 3690: 123, 3720: 124, 3780: 126, 3840: 128, 3870: 129,
    3960: 132, 4050: 135, 4080: 136, 4140: 138, 4200: 140, 4230: 141, 4320: 144, 4410: 147,
    4440: 148, 4500: 150, 4560: 152, 4590: 153, 4680: 156, 4770: 159, 4800: 160, 4860: 162,
    4920: 164, 4950: 165, 5040: 168, 5130: 171, 5160: 172, 5220: 174, 5280: 176, 5310: 177,
    5400: 180, 5520: 184, 5640: 188, 5760: 192, 5880: 196, 6000: 200, 6120: 204, 6240: 208,
    6360: 212, 6480: 216, 6600: 220, 6720: 224, 6840: 228, 6960: 232, 7080: 236, 7200: 240,
}

# ========================================================

annual_pricing_table = {
    1080: 2, 1596: 3, 2100: 4, 2580: 5, 3060: 6, 3516: 7, 3948: 8, 4380: 9,
    4788: 10, 5172: 11, 5556: 12, 5916: 13, 6264: 14, 6600: 15, 6912: 16, 7212: 17,
    7500: 18, 7764: 19, 8028: 20, 8268: 21, 8484: 22, 8700: 23, 8892: 24, 9060: 25,
    9228: 26, 9372: 27, 9504: 28, 9624: 29, 9720: 30, 10044: 31, 10368: 32, 10692: 33,
    11016: 34, 11340: 35, 11664: 36, 11988: 37, 12312: 38, 12636: 39, 12960: 40, 13284: 41,
    13608: 42, 13932: 43, 14256: 44, 14580: 45, 14904: 46, 15228: 47, 15552: 48, 15876: 49,
    16200: 50, 16524: 51, 16848: 52, 17172: 53, 17496: 54, 17820: 55, 18144: 56, 18468: 57,
    18792: 58, 19116: 59, 19440: 60, 20088: 62, 20412: 63, 20736: 64, 21384: 66, 22032: 68,
    22356: 69, 22680: 70, 23328: 72, 23976: 74, 24300: 75, 24624: 76, 25272: 78, 25920: 80,
    26244: 81, 26568: 82, 27216: 84, 27864: 86, 28188: 87, 28512: 88, 29160: 90, 29808: 92,
    30132: 93, 30456: 94, 31104: 96, 31752: 98, 32076: 99, 32400: 100, 33048: 102, 33696: 104,
    34020: 105, 34344: 106, 34992: 108, 35640: 110, 35964: 111, 36288: 112, 36936: 114,
    37584: 116, 37908: 117, 38232: 118, 38880: 120, 39852: 123, 40176: 124, 40824: 126,
    41472: 128, 41796: 129, 42768: 132, 43740: 135, 44064: 136, 44712: 138, 45360: 140,
    45684: 141, 46656: 144, 47628: 147, 47952: 148, 48600: 150, 49248: 152, 49572: 153,
    50544: 156, 51516: 159, 51840: 160, 52488: 162, 53136: 164, 53460: 165, 54432: 168,
    55404: 171, 55728: 172, 56376: 174, 57024: 176, 57672: 178, 58320: 180, 59616: 184,
    60912: 188, 62208: 192, 63504: 196, 64800: 200, 66096: 204, 67392: 208, 68688: 212,
    69984: 216, 71280: 220, 72576: 224, 73872: 228, 75168: 232, 76464: 236, 77760: 240,
}

# ========================================================

one_time_pricing_table = {
    60: 1,
    118: 2,
    173: 3,
    227: 4,
    278: 5,
    327: 6,
    373: 7,
    418: 8,
    460: 9,
    500: 10,
}

# ========================================================

def get_plan_from_total(total: int):
    if total in monthly_pricing_table:
        return "monthly"
    elif total in annual_pricing_table:
        return "annual"
    elif total in one_time_pricing_table:
        return "onetime"
    return None

# ========================================================

def calculate_credits(plan: str, total: int) -> int:
    if plan == "monthly":
        return monthly_pricing_table.get(total, 0)
    elif plan == "annual":
        return annual_pricing_table.get(total, 0)
    elif plan == "onetime":
        return one_time_pricing_table.get(total, 0)
    return 0

# ========================================================

def verify_access_token(access_token):
    if not access_token:
        return {"error": "AccessToken is required"}, 403

    response = supabase.table("clientbase").select("*").eq("access_token", access_token).execute()
    if not response.data:
        return {"error": f"AccessToken '{access_token}' not found"}, 403

    return {"message": "AccessToken is valid"}, 200

# ========================================================

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

# ========================================================

def load_card_token(invoice_id):
    try:
        response = requests.get(f"{MONOBANK_API_BASEURL}merchant/invoice/status?invoiceId={invoice_id}",
                                headers={"X-Token": MONOBANK_API_KEY})
        card_token = response.json().get("walletData", {}).get("cardToken", None)
        if card_token:
            return card_token
        else:
            logging.error(f"No card token found in response: {response.json()}")
            return None
    except Exception as e:
        logging.error(f"Error loading card token: {e}")
        return None

# ========================================================

def update_payment_info(data):
    total_str = data.get("destination", "")
    if not total_str.isdigit():
        return

    total = int(total_str)
    access_token = data.get("reference")
    invoice_id = data.get("invoiceId")

    card_token = load_card_token(invoice_id)
    plan = get_plan_from_total(total)

    subscription_period = 30 if plan == "monthly" else 365 if plan == "annual" else None

    utc_timezone = pytz.utc
    current_time = datetime.datetime.now(tz=utc_timezone)
    iso_time_str = current_time.isoformat()

    if subscription_period:
        new_payment_info = {
            "subscription_amount": total,
            "subscription_period": subscription_period,
            "last_subscription_transaction": iso_time_str
        }
        if card_token:
            new_payment_info["card_token"] = card_token

        supabase.table("clientbase").update(new_payment_info).eq("access_token", access_token).execute()

# ========================================================

def process_monobank_payment_webhook(data):
    try:
        logging.info("Webhook data: %s", data)
        
        payment_status = data.get("status")
        access_token = data.get("reference")
        invoice_id = data.get("invoiceId")
        logging.info("Invoice ID received: %s", invoice_id)
        
        total_str = data.get("destination", "")
        if not total_str.isdigit():
            logging.error("Invalid destination value:", total_str)
            return {"error": "Invalid webhook data"}, 400

        total = int(total_str)
        if not access_token or not total or not invoice_id:
            logging.error("Missing required data:", access_token, total, invoice_id)
            return {"error": "Invalid webhook data"}, 400

        if payment_status == "success":
            existing = supabase.table("transactions").select("*").eq("invoiceId", invoice_id).execute()
            logging.info("Existing transactions for invoice:", existing.data)
            if existing.data:
                logging.info("Transaction already processed, skipping credit update.")
                return {"message": "Transaction already processed"}, 200

            response = supabase.table("clientbase").select("current_credits, slack_id").eq("access_token", access_token).execute()
            if response.data:
                client = response.data[0]
                current_credits = client.get("current_credits", 0)
                slack_id = client.get("slack_id")
                plan = get_plan_from_total(total)
                added_credits = calculate_credits(plan, total)
                new_credits = current_credits + added_credits

                supabase.table("clientbase").update({"current_credits": new_credits}).eq("access_token", access_token).execute()
                
                update_payment_info(data)

                supabase.table("transactions").insert({"invoiceId": invoice_id, "status": "processed"}).execute()
                logging.info("Inserted transaction for invoice:", invoice_id)

                if plan == "onetime":
                    text_msg = (f"The purchase of {added_credits} credits was successful. "
                                f"Your total balance is now {current_credits} + {added_credits} = {new_credits} credits.")
                elif plan == "annual":
                    activate_client_subscription(slack_id)
                    text_msg = (f"The purchase of an annual subscription with {added_credits} credits was successful. "
                                f"Your total balance is now {current_credits} + {added_credits} = {new_credits} credits.")
                elif plan == "monthly":
                    activate_client_subscription(slack_id)
                    text_msg = (f"The purchase of a monthly subscription with {added_credits} credits was successful. "
                                f"Your total balance is now {current_credits} + {added_credits} = {new_credits} packages.")
                else:
                    text_msg = f"The purchase was successful. Your total balance is now {new_credits} packages."

                if slack_id:
                    slack_app.client.chat_postMessage(channel=slack_id, text=text_msg)
                else:
                    logging.error("No slack_id found for user with access_token:", access_token)

                return {"message": "Credits updated successfully"}, 200

        logging.error("Payment not successful or invalid status:", payment_status)
        return {"error": "Payment not successful or invalid status"}, 400

    except Exception as e:
        logging.error("Error in process_monobank_payment_webhook:", e)
        return {"error": str(e)}, 500