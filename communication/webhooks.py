import os
import requests
import logging
from flask import request, jsonify
from slack_bolt.adapter.flask import SlackRequestHandler
from .asana_utils import move_task_to_archive
from .commands import app
from config.config import ASANA_ADMIN_ID
from generation.thumbnails_generation import thumbnail_revision
from database.database import get_deliverables_by_task_id


from database.database import (
    fetch_client_data,
    fetch_client_data_by_task_id,
    update_client_thread_mapping,
    remove_task_from_current_tasks,
    remove_thread_mappings_for_task,
    update_task_history
)

# ========================================================

handler = SlackRequestHandler(app)

# ========================================================

GREETING_MESSAGE = "Hi {name}, the deliverables for your video are ready, please take a look!"

# ========================================================

def split_text_to_blocks(text, chunk_size=3000):
    blocks = []
    while text:
        if len(text) <= chunk_size:
            chunk = text
            text = ""
        else:
            split_at = text.rfind(" ", 0, chunk_size)
            if split_at == -1:
                split_at = chunk_size
            chunk = text[:split_at].strip()
            text = text[split_at:].strip()

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": chunk}
        })

    return blocks

# ========================================================

def asana_webhook():
    if "X-Hook-Secret" in request.headers:
        return jsonify({}), 200, {"X-Hook-Secret": request.headers["X-Hook-Secret"]}

    data = request.json
    if data and "events" in data:
        for event in data["events"]:
            if event.get("action") == "added" and event["resource"].get("resource_subtype") == "comment_added":
                task_id = event["parent"]["gid"]
                comment_gid = event["resource"]["gid"]

                comment_url = f"https://app.asana.com/api/1.0/stories/{comment_gid}"
                headers = {"Authorization": f"Bearer {os.getenv('ASANA_ACCESS_TOKEN')}"}
                comment_response = requests.get(comment_url, headers=headers)
                if comment_response.status_code != 200:
                    logging.error("Failed to fetch comment: %s", comment_response.text)
                    continue

                comment_data = comment_response.json().get("data", {})
                comment_text = comment_data.get("text", "")
                comment_author_id = comment_data.get("created_by", {}).get("gid")

                # ==========

                if comment_author_id == ASANA_ADMIN_ID and "FINAL_OUTPUT_START" not in comment_text:
                    continue

                # if comment_author_id == ASANA_ADMIN_ID:
                #     continue

                if "FINAL_OUTPUT_START" in comment_text:
                    comment_text = comment_text.replace("🎁 FINAL_OUTPUT_START", "").replace("🎁 FINAL_OUTPUT_END", "").strip()

                # ===========

                client_info = fetch_client_data_by_task_id(task_id)
                if not client_info:
                    logging.error(f"No client info found for task ID: {task_id}")
                    continue

                thread_mappings = client_info.get("thread_mappings") or {}
                thread_ts = next((k for k, v in thread_mappings.items() if v == task_id), None)

                greeting = GREETING_MESSAGE.format(name=client_info.get("client_name_short", "there"))

                if not thread_ts:
                    response = app.client.chat_postMessage(
                            channel=client_info["slack_id"],
                        text=f"*{greeting}* \n\n{comment_text}",
                        # blocks=[
                        #     {
                        #         "type": "section",
                        #         "text": {"type": "mrkdwn", "text": f"*{greeting}* \n\n{comment_text}"},
                        #     },
                        #     {
                        #         "type": "actions",
                        #         "elements": [
                        #             {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "action_id": "accept_work", "value": str(task_id)},
                        #             {"type": "button", "text": {"type": "plain_text", "text": "Request Revisions"}, "action_id": "request_revisions"},
                        #         ],
                        #     },
                        # ],
                        blocks=[
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": f"*{greeting}*"},
                            },
                            *split_text_to_blocks(comment_text),
                            {
                                "type": "actions",
                                "elements": [
                                    {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "action_id": "accept_work", "value": str(task_id)},
                                    {"type": "button", "text": {"type": "plain_text", "text": "Request Revisions"}, "action_id": "request_revisions", "value": str(task_id)},
                                ],
                            },
                        ]
                    )
                    thread_ts = response["ts"]

                    update_client_thread_mapping(client_info["slack_id"], thread_ts, task_id)

                else:
                    app.client.chat_postMessage(
                        channel=client_info["slack_id"],
                        text=comment_text,
                        thread_ts=thread_ts,
                        # blocks=[
                        #     {
                        #         "type": "section",
                        #         "text": {"type": "mrkdwn", "text": comment_text},
                        #     },
                        #     {
                        #         "type": "actions",
                        #         "elements": [
                        #             {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "action_id": "accept_work", "value": str(task_id)},
                        #             {"type": "button", "text": {"type": "plain_text", "text": "Request Revisions"}, "action_id": "request_revisions"},
                        #         ],
                        #     },
                        # ],
                        blocks=[
                            *split_text_to_blocks(comment_text),
                            {
                                "type": "actions",
                                "elements": [
                                    {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "action_id": "accept_work", "value": str(task_id)},
                                    {"type": "button", "text": {"type": "plain_text", "text": "Request Revisions"}, "action_id": "request_revisions", "value": str(task_id)},
                                ],
                            },
                        ]
                    )

                    update_client_thread_mapping(client_info["slack_id"], thread_ts, task_id)

        return jsonify({"status": "success"}), 200

    return jsonify({"status": "failure"}), 400

# ========================================================

@app.action("accept_work")
def handle_accept_work(ack, body, client):
    ack()

    channel_id = body["channel"]["id"]
    message_ts = body["message"]["ts"]
    response_url = body["response_url"]

    client_info = fetch_client_data(channel_id)
    if client_info:
        task_id = body.get("actions")[0].get("value")
        if task_id:
            move_task_to_archive(task_id)
            remove_thread_mappings_for_task(channel_id, task_id)
            remove_task_from_current_tasks(channel_id, task_id)
            update_task_history(channel_id, task_id)

            try:
                original_message = client.conversations_replies(
                    channel=channel_id,
                    ts=message_ts
                )
                if original_message["ok"] and original_message["messages"]:
                    full_message = original_message["messages"][0].get("text", "")
                    greeting = GREETING_MESSAGE.format(name=client_info.get("client_name_short", "there"))
                    designer_message = full_message.replace(f"*{greeting}*", "").strip()
                else:
                    designer_message = ""

                requests.post(
                    response_url,
                    json={
                        "replace_original": True,
                        "text": f"{designer_message}"
                    }
                )

                client.chat_postMessage(
                    channel=channel_id,
                    text="This request has been approved. Thank you!",
                    thread_ts=message_ts
                )

            except Exception as e:
                logging.error(f"Error while handling approval: {e}")
        else:
            logging.error("No task ID found to archive")
    else:
        logging.error("Client information not found.")

# ========================================================

@app.action("request_revisions")
def handle_request_revisions(ack, body, client):
    ack()

    channel_id = body["channel"]["id"]
    message_ts = body["message"]["ts"]
    response_url = body["response_url"]

    client_info = fetch_client_data(channel_id)
    if client_info:
        thread_ts = message_ts
        # task_id = client_info.get("thread_mappings", {}).get(thread_ts)
        task_id = body.get("actions")[0].get("value")

        if not task_id:
            current_tasks = client_info.get("current_tasks", "").split(",")
            task_id = current_tasks[0] if current_tasks else None

        if task_id:
            try:
                original_message = client.conversations_replies(
                    channel=channel_id,
                    ts=thread_ts
                )
                
                if original_message["ok"] and original_message["messages"]:
                    full_message = original_message["messages"][0].get("text", "")
                    greeting = GREETING_MESSAGE.format(name=client_info.get("client_name_short", "there"))
                    designer_message = full_message.replace(f"*{greeting}*", "").strip()
                else:
                    designer_message = ""

                updated_text = (
                    f"{designer_message}"
                )
                
                client.chat_update(
                    channel=channel_id,
                    ts=message_ts,
                    text=updated_text
                )
                
                thread_message = client.chat_postMessage(
                    channel=channel_id,
                    text="Please provide your revisions below.",
                    thread_ts=thread_ts,
                )

                if thread_message["ok"]:
                    update_client_thread_mapping(channel_id, thread_ts, task_id)
                    requests.post(
                        response_url,
                        json={
                            "replace_original": True,
                            "text": updated_text
                        }
                    )

                else:
                    logging.error("Failed to post message in thread: %s", thread_message)

            except Exception as e:
                logging.error(f"Error while posting message to Slack thread: {e}")
        else:
            logging.error("No task ID found for this thread.")
    else:
        logging.error("Client information not found.")

# ========================================================

@app.event("message")
def handle_thread_messages(event, say, client):
    if "thread_ts" in event and not event.get("bot_id"):
        thread_ts = event["thread_ts"]
        channel_id = event["channel"]
        user_message = event.get("text", "")

        client_info = fetch_client_data(channel_id)
        if client_info:
            thread_mappings = client_info.get("thread_mappings", {})
            task_id = thread_mappings.get(thread_ts)

            if task_id:
                headers = {
                    "Authorization": f"Bearer {os.getenv('ASANA_ACCESS_TOKEN')}",
                    "Content-Type": "application/json"
                }
                comment_url = f"https://app.asana.com/api/1.0/tasks/{task_id}/stories"
                data = {"data": {"text": user_message}}
                requests.post(comment_url, headers=headers, json=data)

                client.reactions_add(
                    channel=channel_id,
                    name="eyes",
                    timestamp=event["ts"]
                )

                # if not client_info.get("is_client_vip", False):
                #     thumbnail_revision(task_id, user_message)

                if not client_info.get("is_client_vip", False):
                    full_data = get_deliverables_by_task_id(channel_id, task_id)
                    if full_data:
                        thumbnail_revision(task_id, user_message, full_data)