from flask import Flask
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from database import (
    fetch_client_data,
    update_client_credits,
    update_client_current_tasks,
    get_access_token
)
from asana_utils import create_asana_task, register_webhook_for_task, create_asana_subtask
from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, BACKEND_BASEURL

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
                        {"text": {"type": "plain_text", "text": "3 packages"}, "value": "3"},
                        {"text": {"type": "plain_text", "text": "4 packages"}, "value": "4"}
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
        try:
            access_token = get_access_token(channel_id)
            payment_url = f"{BACKEND_BASEURL}pricing/{access_token}"
            app.client.chat_postMessage(
                channel=channel_id,
                text=(
                    f"Hi {client_info.get('client_name_short', ' ')}! "
                    f"You currently have *{client_info.get('current_credits', 'N/A')}* credits left.\n\n"
                    f"If you need more credits, refill your account <{payment_url}|here>."
                )
            )
        except ValueError as e:
            app.client.chat_postMessage(
                channel=channel_id,
                text=f"*Error:* {str(e)}. Please contact support for assistance.\n\n"
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

    package_credits_map = {"1": 1, "2": 2, "3": 3, "4": 4}
    required_credits = package_credits_map.get(thumbnail_packages, 1)

    client_info = fetch_client_data(channel_id)
    if not client_info:
        client.chat_postMessage(channel=channel_id, text="*Error:* Unable to fetch your client data.")
        return

    current_credits = client_info.get("current_credits", 0)
    if current_credits < required_credits:
        access_token = get_access_token(channel_id)
        payment_url = f"{BACKEND_BASEURL}pricing/{access_token}"
        client.chat_postMessage(
            channel=channel_id,
            text=(
                f"*Sorry, seems you don't have enough credits. "
                f"Please refill the <{payment_url}|tank> and try again.*"
            )
        )
        return

    # This is the detailed order info that will go inside the subtask.
    task_notes = f"""ORDER INFORMATION
Packages amount: {thumbnail_packages}
Resizes: {client_info.get('resize', 'None')}.

AUTHOR INFORMATION
Author's name: {client_info.get('client_name_full', 'Unknown')}
Channel link: {client_info.get('client_channel_link', 'Unknown')}
Author's photo: {client_info.get('face_photos', 'None')}

STYLE
Author's branding: {client_info.get('branding', 'None')}
Author's preferences: {client_info.get('client_wishes', 'Unknown')}

TASK DESCRIPTION
Video Link: {video_link}
Additional Info: {additional_info}
"""

    # This is the simple description for the main task (like four empty rooms)
    main_task_description = (
        "1.\nThumbnail:\nTitle:\nDescription:\n\n"
        "2.\nThumbnail:\nTitle:\nDescription:\n\n"
        "3.\nThumbnail:\nTitle:\nDescription:\n\n"
        "4.\nThumbnail:\nTitle:\nDescription:\n\n"
        "Links for converting images - https://uk.imgbb.com/"
    )

    task_name = f"Request from {client_info.get('client_name_short', 'Unknown')}"
    # Create the main task in Asana using the simple description
    main_task_id = create_asana_task(task_name, main_task_description)

    if main_task_id:
        # Now create a subtask inside the main task using the detailed order info.
        subtask_name = "Order Details"
        subtask_id = create_asana_subtask(main_task_id, subtask_name, task_notes)
        
        update_client_current_tasks(channel_id, main_task_id)
        register_webhook_for_task(main_task_id)
        update_client_credits(channel_id, current_credits - required_credits)
        client.chat_postMessage(
            channel=channel_id,
            text=(
                f"*Your request with the following details has been received. Thank you!* \n\n" 
                f"*Link to the video:* {video_link} \n\n"
                f"*Additional information:* {additional_info} \n\n"
                f"*Amount of packages:* {thumbnail_packages} \n\n"
                f"*Resizes:* {client_info.get('resize', 'None')} \n\n"
            )
        )
    else:
        client.chat_postMessage(
            channel=channel_id,
            text="*Error:* Unable to create a task in Asana. Please try again later."
        )