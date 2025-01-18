import os
import json
import requests
from flask import request, jsonify
from slack_bolt.adapter.flask import SlackRequestHandler

from config import SLACK_BOT_TOKEN, SLACK_API_URL, ASANA_ADMIN_ID
from database import (
    fetch_client_data,
    fetch_client_data_by_task_id,
    update_client_thread_mapping,
    remove_task_from_current_tasks,
    remove_thread_mappings_for_task,
    update_task_history
)
from asana_utils import move_task_to_archive
from commands import app

handler = SlackRequestHandler(app)

GREETING_MESSAGE = "Hi {name}, the deliverables for your video are ready. Please review them and choose whether you are satisfied, or if you'd like to request changes."

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
                    print("Failed to fetch comment:", comment_response.text)
                    continue

                comment_data = comment_response.json().get("data", {})
                comment_text = comment_data.get("text", "")
                comment_author_id = comment_data.get("created_by", {}).get("gid")

                if comment_author_id == ASANA_ADMIN_ID:
                    continue

                client_info = fetch_client_data_by_task_id(task_id)
                if not client_info:
                    print(f"No client info found for task ID: {task_id}")
                    continue

                thread_mappings = client_info.get("thread_mappings") or {}
                thread_ts = next((k for k, v in thread_mappings.items() if v == task_id), None)

                greeting = GREETING_MESSAGE.format(name=client_info.get("client_name_short", "there"))

                if not thread_ts:
                    response = app.client.chat_postMessage(
                        channel=client_info["slack_id"],
                        text=f"*{greeting}* \n\n{comment_text}",
                        blocks=[
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": f"*{greeting}* \n\n{comment_text}"},
                            },
                            {
                                "type": "actions",
                                "elements": [
                                    {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "action_id": "accept_work"},
                                    {"type": "button", "text": {"type": "plain_text", "text": "Request Revisions"}, "action_id": "request_revisions"},
                                ],
                            },
                        ],
                    )
                    thread_ts = response["ts"]
                    # print(f"Created new thread: {thread_ts}")

                    update_client_thread_mapping(client_info["slack_id"], thread_ts, task_id)

                else:
                    app.client.chat_postMessage(
                        channel=client_info["slack_id"],
                        text=comment_text,
                        thread_ts=thread_ts,
                        blocks=[
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": comment_text},
                            },
                            {
                                "type": "actions",
                                "elements": [
                                    {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "action_id": "accept_work"},
                                    {"type": "button", "text": {"type": "plain_text", "text": "Request Revisions"}, "action_id": "request_revisions"},
                                ],
                            },
                        ],
                    )

                    update_client_thread_mapping(client_info["slack_id"], thread_ts, task_id)

        return jsonify({"status": "success"}), 200

    return jsonify({"status": "failure"}), 400

def slack_actions():
    payload = request.form["payload"]
    data = json.loads(payload)

    action = data.get("actions")[0]
    channel_id = data["channel"]["id"]
    response_url = data["response_url"]
    message_ts = data["message"]["ts"]

    if action["action_id"] == "accept_work":
        client_info = fetch_client_data(channel_id)
        if client_info:
            task_id = client_info.get("current_tasks", "").split(",")[0]
            if task_id:
                # print(f"Archiving Task ID: {task_id}")
                move_task_to_archive(task_id)

                remove_thread_mappings_for_task(channel_id, task_id)
                remove_task_from_current_tasks(channel_id, task_id)
                update_task_history(channel_id, task_id)

                try:
                    original_message = app.client.conversations_replies(
                        channel=channel_id,
                        ts=message_ts
                    )
                    if original_message["ok"] and original_message["messages"]:
                        full_message = original_message["messages"][0].get("text", "")
                        greeting = GREETING_MESSAGE.format(name=client_info.get("client_name_short", "there"))
                        designer_message = full_message.replace(f"*{greeting}*", "").strip()
                    else:
                        designer_message = ""

                    app.client.chat_postMessage(
                        channel=channel_id,
                        text="This request has been approved. Thank you!",
                        thread_ts=message_ts
                    )

                except Exception as e:
                    print(f"Error while handling approval: {e}")

                requests.post(
                    response_url,
                    json={
                        "replace_original": True,
                        "text": f"{designer_message}"
                    }
                )
            else:
                print("No task ID found to archive")
        else:
            print("Could not find client info")
        return jsonify({"status": "success"})

    elif action["action_id"] == "request_revisions":
        client_info = fetch_client_data(channel_id)
        if client_info:
            thread_ts = message_ts
            task_id = client_info.get("thread_mappings", {}).get(thread_ts)

            if not task_id:
                current_tasks = client_info.get("current_tasks", "").split(",")
                task_id = current_tasks[0] if current_tasks else None

            if task_id:
                # print(f"Requesting revisions for Task ID: {task_id}, Thread TS: {thread_ts}")

                try:
                    original_message = app.client.conversations_replies(
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
                    app.client.chat_update(
                        channel=channel_id,
                        ts=message_ts,
                        text=updated_text
                    )
                    thread_message = requests.post(
                        f"{SLACK_API_URL}/chat.postMessage",
                        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                        json={
                            "channel": channel_id,
                            "text": "Please provide your revisions below.",
                            "thread_ts": thread_ts,
                        },
                    )
                    # print(f"Slack API Response: {thread_message.status_code} - {thread_message.text}")

                    if thread_message.status_code == 200:
                        update_client_thread_mapping(channel_id, thread_ts, task_id)
                        # print(f"Updated thread mappings with Thread TS: {thread_ts}, Task ID: {task_id}")

                        requests.post(
                            response_url,
                            json={
                                "replace_original": True,
                                "text": updated_text
                            }
                        )
                        return jsonify({"status": "success"})
                    else:
                        print("Failed to post message in thread:", thread_message.text)
                        return jsonify({"status": "failure", "error": "Failed to post message in thread"}), 500
                except Exception as e:
                    print(f"Error while posting message to Slack thread: {e}")
                    return jsonify({"status": "failure", "error": str(e)}), 500
            else:
                print("No task ID found for this thread.")
        else:
            print("Client information not found.")

        return jsonify({"status": "failure", "message": "Action not handled properly"}), 400

@app.event("message")
def handle_thread_messages(event, say):
    # print(f"Received message event: {event}")

    if "thread_ts" in event:
        thread_ts = event["thread_ts"]
        channel_id = event["channel"]
        user_message = event.get("text", "")

        # print(f"Thread TS: {thread_ts}, Channel ID: {channel_id}, Message: {user_message}")

        client_info = fetch_client_data(channel_id)
        if client_info:
            thread_mappings = client_info.get("thread_mappings", {})
            # print(f"Thread Mappings in Database: {thread_mappings}")

            task_id = thread_mappings.get(thread_ts)
            # print(f"Resolved Task ID: {task_id}")

            current_tasks = client_info.get("current_tasks", "").split(",")
            if task_id not in current_tasks:
                # print(f"Task ID {task_id} is not active. Ignoring message in thread {thread_ts}.")
                return

            if task_id:
                headers = {
                    "Authorization": f"Bearer {os.getenv('ASANA_ACCESS_TOKEN')}",
                    "Content-Type": "application/json"
                }
                comment_url = f"https://app.asana.com/api/1.0/tasks/{task_id}/stories"
                data = {"data": {"text": user_message}}
                response = requests.post(comment_url, headers=headers, json=data)

                # print(f"Asana API Response: {response.status_code} - {response.text}")

                if response.status_code == 201:
                    say(text="Your revisions have been received!", thread_ts=thread_ts)
                else:
                    say(text="Failed to send your revision. Please try again.", thread_ts=thread_ts)
            else:
                say(text="Could not find a corresponding Asana task for this thread.", thread_ts=thread_ts)
        else:
            say(text="Could not find client information.", thread_ts=thread_ts)