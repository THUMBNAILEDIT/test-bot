import json
import logging

def filtered_videos_analysis(filtered_videos):
    logging.info("Videos ready to be filtered:")
    logging.info(json.dumps(filtered_videos, indent=4, ensure_ascii=False))