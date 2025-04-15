import re
import requests
import logging
from communication.task_details import get_task_details, add_to_task_details
from config.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, GOOGLE_TOKEN_URI
from context.video_context_analysis import get_video_context, create_video_description, get_video_query

logging.basicConfig(level=logging.INFO)

def get_access_token():
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }

    response = requests.post(GOOGLE_TOKEN_URI, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def fetch_google_doc_content(video_link):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', video_link)
    if not match:
        logging.error("Failed to extract document ID from link: %s", video_link)
        return None
    doc_id = match.group(1)

    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(
            f"https://docs.googleapis.com/v1/documents/{doc_id}",
            headers=headers
        )
        response.raise_for_status()
        doc = response.json()
    except Exception as e:
        logging.error("Error fetching document: %s", e)
        return None

    video_script = ""
    for element in doc.get('body', {}).get('content', []):
        if 'paragraph' in element:
            for el in element['paragraph'].get('elements', []):
                if 'textRun' in el and 'content' in el['textRun']:
                    video_script += el['textRun']['content']

    add_to_task_details("video_script", video_script)
    additional_info = get_task_details("additional_info")

    get_video_context(video_script, additional_info)
    create_video_description(video_script, additional_info)
    get_video_query(video_script, additional_info)

    return video_script