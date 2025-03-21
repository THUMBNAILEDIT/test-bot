import requests
import json
import logging
from datetime import datetime, timedelta, timezone
from config.config import YOUTUBE_DATA_API_KEY
from .youtube_filter import check
# from communication.task_details import get_task_details, delete_from_task_details, add_to_task_details

logging.basicConfig(level=logging.INFO)

YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
YOUTUBE_VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos'

def youtube_search(video_query):
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    published_after = one_month_ago.isoformat()

    params = {
        'part': 'snippet',
        'q': video_query,
        'type': 'video',
        'maxResults': 10,
        'videoDuration': 'medium',
        'order': 'viewCount',
        'publishedAfter': published_after,
        'key': YOUTUBE_DATA_API_KEY
    }
    response = requests.get(YOUTUBE_SEARCH_URL, params=params)
    if response.status_code != 200:
        logging.error(f"Request error: {response.text}")
        return

    data = response.json()
    video_ids = [item['id']['videoId'] for item in data.get('items', [])]

    params_videos = {
        'part': 'snippet,statistics,contentDetails',
        'id': ','.join(video_ids),
        'key': YOUTUBE_DATA_API_KEY
    }
    response_videos = requests.get(YOUTUBE_VIDEOS_URL, params=params_videos)
    if response_videos.status_code != 200:
        logging.error(f"Videos request error: {response_videos.text}")
        return

    # searched_videos = response_videos.json().get('items', [])
    # pretty_details = json.dumps(searched_videos, indent=4, ensure_ascii=False) – all the available information about the video
    # logging.info(pretty_details)

    searched_videos = response_videos.json().get('items', [])
    
    found_videos = []
    
    now = datetime.now(timezone.utc)
    
    for searched_video in searched_videos:
        snippet = searched_video.get('snippet', {})
        statistics = searched_video.get('statistics', {})
        published_at = snippet.get('publishedAt')

        if published_at:
            published_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            age_delta = now - published_dt
            if age_delta.days >= 1:
                age = age_delta.days
            else:
                age = age_delta.seconds // 3600
        else:
            age = None

        thumbnail = snippet.get('thumbnails', {}).get('maxres', {}).get('url') or \
                    snippet.get('thumbnails', {}).get('high', {}).get('url')
        
        video_obj = {
            "title": snippet.get("title"),
            "thumbnail": thumbnail,
            "viewCount": statistics.get("viewCount"),
            "likeCount": statistics.get("likeCount"),
            "age": age
        }
        
        found_videos.append(video_obj)

    check(found_videos)

    # pretty_details = json.dumps(found_videos, indent=4, ensure_ascii=False)
    # logging.info(pretty_details)