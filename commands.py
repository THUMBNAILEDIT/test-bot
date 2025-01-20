from flask import Flask
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from database import (
    fetch_client_data,
    update_client_credits,
    update_client_current_tasks,
)
from asana_utils import create_asana_task, register_webhook_for_task
from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@app.command("/request")
def handle_request(ack, body, client):
    ack()
    user_id = body["user_id"]

    modal_view = {
        "type": "modal",
        "callback_id": "request_modal_submission",
        "title": {"type": "plain_text", "text": "New request"},
        "private_metadata": body["channel_id"],
        "blocks": [
            {
                "type": "input",
                "block_id": "video_link",
                "label": {"type": "plain_text", "text": "Link to your video"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input",
                    "placeholder": {"type": "plain_text", "text": "Make sure the link is accessible :)"}
                },
            },
            {
                "type": "input",
                "block_id": "additional_info",
                "label": {"type": "plain_text", "text": "Additional information about your video"},
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Not necessary, but always welcomed"}
                },
            },
            {
                "type": "input",
                "block_id": "thumbnail_packages",
                "label": {"type": "plain_text", "text": "Number of packages needed"},
                "element": {
                    "type": "static_select",
                    "action_id": "select",
                    "placeholder": {"type": "plain_text", "text": "Select an option"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "1 package"}, "value": "1"},
                        {"text": {"type": "plain_text", "text": "2 packages"}, "value": "2"},
                        {"text": {"type": "plain_text", "text": "3 packages"}, "value": "3"}
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "resizes_needed",
                "label": {"type": "plain_text", "text": "Resizes needed"},
                "element": {
                    "type": "multi_static_select",
                    "action_id": "select",
                    "placeholder": {"type": "plain_text", "text": "Select options"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "No resizes needed"}, "value": "No resizes needed"},
                        {"text": {"type": "plain_text", "text": "Social media post (1080x1080)"}, "value": "Social media post (1080x1080)"},
                        {"text": {"type": "plain_text", "text": "Vertical video cover (1080x1920)"}, "value": "Vertical video cover (1080x1920)"},
                    ]
                }
            }
        ],
        "submit": {"type": "plain_text", "text": "Submit"}
    }

    client.views_open(trigger_id=body["trigger_id"], view=modal_view)

@app.command("/balance")
def handle_balance(ack, command):
    ack()
    channel_id = command["channel_id"]
    client_info = fetch_client_data(channel_id)
    
    if client_info:
        app.client.chat_postMessage(
            channel=channel_id,
            text=(
                f"Hi {client_info.get('client_name_short', ' ')}! "
                f"You currently have *{client_info.get('current_credits', 'N/A')}* credits left. "
            )
        )
    else:
        app.client.chat_postMessage(
            channel=channel_id,
            text="*Error:* We couldn't find your client info. Please ensure your Slack channel is registered.\n\n"
        )

@app.view("request_modal_submission")
def handle_modal_submission(ack, body, client):
    ack()

    state_values = body["view"]["state"]["values"]
    user_id = body["user"]["id"]
    channel_id = body["view"]["private_metadata"]

    video_link = state_values["video_link"]["input"]["value"]
    
    additional_info = state_values.get("additional_info", {}).get("input", {}).get("value")
    if additional_info:
        additional_info = additional_info.strip()
        if not additional_info or additional_info in [".", ",", "-", "_"]:
            additional_info = "No additional information"
    else:
        additional_info = "No additional information"

    thumbnail_packages = state_values["thumbnail_packages"]["select"]["selected_option"]["value"]
    resizes_needed = [
        option["value"]
        for option in state_values["resizes_needed"]["select"]["selected_options"]
    ]

    package_credits_map = {"1": 1, "2": 2, "3": 3}
    required_credits = package_credits_map.get(thumbnail_packages, 1)

    client_info = fetch_client_data(channel_id)
    if not client_info:
        client.chat_postMessage(channel=channel_id, text="*Error:* Unable to fetch your client data.")
        return

    current_credits = client_info.get("current_credits", 0)
    if current_credits < required_credits:
        client.chat_postMessage(
            channel=channel_id,
            text=(
                "*Sorry, seems you don't have enough credits. "
                "Please refill the tank and try again.*"
            )
        )
        return

    task_notes = f"""ORDER INFORMATION
Order type: YouTube Thumbnail
Main deliverables:
    • 1920 x 1080 image (.JPG)
    • Project file (.PSD)
Thumbnail packages amount: {thumbnail_packages}
Additional resizes: {", ".join(resizes_needed)}

CLIENT INFORMATION
Client: {client_info.get('client_name_full', 'Unknown')} 
Client's channel: {client_info.get('client_channel_name', 'Unknown')} ({client_info.get('client_channel_link', 'Unknown')})

STYLE
Client's preferences: {client_info.get('client_preferences', 'Unknown')}
Thumbnail examples: {client_info.get('client_thumbnail_examples', 'Unknown')}

TASK DESCRIPTION
Video Link: {video_link}
Additional Info: {additional_info}
"""

    task_name = f"Request from {client_info.get('client_name_short', 'Unknown')}"
    task_id = create_asana_task(task_name, task_notes)

    if task_id:
        update_client_current_tasks(channel_id, task_id)
        register_webhook_for_task(task_id)
        update_client_credits(channel_id, current_credits - required_credits)
        client.chat_postMessage(
            channel=channel_id,
            text=(
                f"*Your request with the following details has been received. Thank you!* \n\n" 
                f"*Link to the video:* {video_link} \n\n"
                f"*Additional information:* {additional_info} \n\n"
                f"*Amount of packages:* {thumbnail_packages} \n\n"
                f"*Requested resizes:* {', '.join(resizes_needed)} \n\n"
            )
        )
    else:
        client.chat_postMessage(
            channel=channel_id,
            text="*Error:* Unable to create a task in Asana. Please try again later."
        )