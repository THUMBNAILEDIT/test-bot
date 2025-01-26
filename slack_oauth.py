from flask import request, jsonify
import requests
from logger import logger
from config import SLACK_CLIENT_ID, SLACK_CLIENT_SIGNING_SECRET

def handle_oauth_callback():
    code = request.args.get("code")
    if not code:
        return "Error: authorization code is missing.", 400

    response = requests.post("https://slack.com/api/oauth.v2.access", data={
        "code": code,
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SIGNING_SECRET,
    })

    data = response.json()
    if not data.get("ok"):
        return f"Slack OAuth error: {data.get('error')}", 400

    logger.info(f"OAuth token received: {data}")
    return jsonify(data)