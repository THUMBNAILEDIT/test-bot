import json
import logging

def check(found_videos):
    logging.info("Launching info in YouTube Filter")
    logging.info(json.dumps(found_videos, indent=4, ensure_ascii=False))