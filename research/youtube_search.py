import re
import requests
import logging
from datetime import datetime, timezone
from config.config import YOUTUBE_DATA_API_KEY

# ========================================================

logging.basicConfig(level=logging.INFO)

YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
YOUTUBE_VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos'

# ========================================================

def parse_duration(duration_str):
    pattern = re.compile(
        r'P'
        r'(?:(?P<days>\d+)D)?'
        r'(?:T'   
        r'(?:(?P<hours>\d+)H)?'
        r'(?:(?P<minutes>\d+)M)?'
        r'(?:(?P<seconds>\d+)S)?'
        r')?'
    )
    
    match = pattern.fullmatch(duration_str)
    
    if not match:
        return 0
    parts = match.groupdict()
    days = int(parts.get("days") or 0)
    hours = int(parts.get("hours") or 0)
    minutes = int(parts.get("minutes") or 0)
    seconds = int(parts.get("seconds") or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds

# ========================================================

def youtube_search(video_query):
    target_count = 20
    found_videos = []
    next_page_token = None

    while len(found_videos) < target_count:
        params = {
            'part': 'snippet',
            'q': video_query,
            'type': 'video',
            'maxResults': 50,
            'order': 'viewCount',
            'key': YOUTUBE_DATA_API_KEY
        }
        if next_page_token:
            params['pageToken'] = next_page_token

        response = requests.get(YOUTUBE_SEARCH_URL, params=params)
        if response.status_code != 200:
            logging.error(f"Request error: {response.text}")
            return found_videos

        data = response.json()
        items = data.get('items', [])
        video_ids = [item['id']['videoId'] for item in items if 'videoId' in item.get('id', {})]
        if not video_ids:
            logging.info("No videos found for query: %s", video_query)
            break

        params_videos = {
            'part': 'snippet,statistics,contentDetails',
            'id': ','.join(video_ids),
            'key': YOUTUBE_DATA_API_KEY
        }
        response_videos = requests.get(YOUTUBE_VIDEOS_URL, params=params_videos)
        if response_videos.status_code != 200:
            logging.error(f"Videos request error: {response_videos.text}")
            return found_videos

        videos = response_videos.json().get('items', [])
        now = datetime.now(timezone.utc)
        for video in videos:
            content_details = video.get('contentDetails', {})
            duration_str = content_details.get('duration')
            if duration_str:
                duration_sec = parse_duration(duration_str)
                if duration_sec < 60:
                    continue
            else:
                continue

            snippet = video.get('snippet', {})
            statistics = video.get('statistics', {})
            published_at = snippet.get('publishedAt')
            if published_at:
                published_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                age_delta = now - published_dt
                age = age_delta.days if age_delta.days >= 1 else age_delta.seconds // 3600
            else:
                age = None

            thumbnail = (snippet.get('thumbnails', {}).get('maxres', {}).get('url')
                         or snippet.get('thumbnails', {}).get('high', {}).get('url'))
            video_obj = {
                "title": snippet.get("title"),
                "thumbnail": thumbnail,
                "viewCount": statistics.get("viewCount"),
                "likeCount": statistics.get("likeCount"),
                "age": age
            }
            found_videos.append(video_obj)
            if len(found_videos) >= target_count:
                break

        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return found_videos[:target_count]