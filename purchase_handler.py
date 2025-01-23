# import requests
# from flask import jsonify
# from database import get_access_token, supabase

# MONOBANK_API_URL = "https://api.monobank.ua/api/merchant/invoice/create"
# MONOBANK_API_KEY = "your_monobank_api_key"

# def handle_purchase(data):
#     try:
#         plan = data.get("plan")
#         total = data.get("total")
#         access_token = data.get("access_token")

#         if not access_token:
#             return jsonify({"error": "AccessToken is required"}), 400

#         client_id = get_access_token(access_token)
#         if not client_id:
#             return jsonify({"error": "Invalid AccessToken"}), 403

#         monobank_payload = {
#             "amount": int(total * 100),
#             "merchantPaymInfo": {
#                 "destination": "Your Purchase",
#                 "reference": access_token
#             }
#         }

#         headers = {"X-Token": MONOBANK_API_KEY}
#         response = requests.post(MONOBANK_API_URL, json=monobank_payload, headers=headers)

#         if response.status_code == 200:
#             monobank_data = response.json()
#             payment_url = monobank_data.get("pageUrl")
#             return jsonify({"payment_url": payment_url}), 200
#         else:
#             return jsonify({"error": "Failed to create payment", "details": response.json()}), 500

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

from flask import jsonify
from database import supabase

def handle_purchase(data):
    try:
        plan = data.get("plan")
        total = data.get("total")
        access_token = data.get("access_token")

        if not access_token:
            return jsonify({"error": "AccessToken is required"}), 400

        response = supabase.table("clientbase").select("*").eq("access_token", access_token).execute()
        if not response.data:
            return jsonify({"error": "Invalid AccessToken"}), 403

        client = response.data[0]
        current_credits = client.get("current_credits", 0)
        new_credits = current_credits + calculate_credits(plan, total)

        supabase.table("clientbase").update({"current_credits": new_credits}).eq("access_token", access_token).execute()

        return jsonify({"message": "Credits updated successfully", "new_credits": new_credits}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
            2592: 4, 4925: 8, 6998: 12, 8813: 16, 10368: 20,
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
    
def verify_access_token(access_token):
    if not access_token:
        return {"error": "AccessToken is required"}, 403

    response = supabase.table("clientbase").select("*").eq("access_token", access_token).execute()
    if not response.data:
        return {"error": f"AccessToken '{access_token}' not found"}, 403

    return {"message": "AccessToken is valid"}, 200