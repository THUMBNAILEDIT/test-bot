import re
import logging
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from communication.task_details import get_task_details, delete_from_task_details, add_to_task_details
from config.config import GOOGLE_DOCS_CREDENTIALS
from context.video_context_analysis import get_video_context, create_video_description, get_video_query

logging.basicConfig(level=logging.INFO)

def fetch_google_doc_content(video_link):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', video_link)
    if not match:
        logging.error("Failed to extract document ID from link: %s", video_link)
        return None
    doc_id = match.group(1)
    
    try:
        creds = Credentials.from_authorized_user_file(
            GOOGLE_DOCS_CREDENTIALS,
            ['https://www.googleapis.com/auth/documents.readonly']
        )
    except Exception as e:
        logging.error("Error loading credentials: %s", e)
        return None
    
    try:
        service = build('docs', 'v1', credentials=creds)
    except Exception as e:
        logging.error("Error building Google Docs service: %s", e)
        return None
    
    try:
        doc = service.documents().get(documentId=doc_id).execute()
    except Exception as e:
        logging.error("Error fetching document: %s", e)
        return None

    video_script = ""
    for element in doc.get('body', {}).get('content', []):
        if 'paragraph' in element:
            for el in element['paragraph'].get('elements', []):
                if 'textRun' in el and 'content' in el['textRun']:
                    video_script += el['textRun']['content']
        
    delete_from_task_details("video_link")
    add_to_task_details("video_script", video_script)
    additional_info = get_task_details("additional_info")

    get_video_context(video_script, additional_info)
    create_video_description(video_script, additional_info)
    get_video_query(video_script, additional_info)

    return video_script