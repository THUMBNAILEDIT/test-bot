import logging
from communication.task_details import get_task_details, delete_from_task_details, add_to_task_details

logging.basicConfig(level=logging.INFO)

def check(video_query):
    updated_details = get_task_details()
    logging.info("Checking video query: %s", video_query)
    logging.info(updated_details)