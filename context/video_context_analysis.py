from openai import OpenAI
import json
import logging
from config.config import OPENAI_API_KEY
from communication.task_details import add_to_task_details
from research.youtube_search import youtube_search
from research.youtube_filter import youtube_filter

client = OpenAI(api_key=OPENAI_API_KEY)

# ========================================================

def get_video_context(video_script, additional_info):
    prompt = (
        "Analyze the following information and provide a concise summary preserving key points.\n\n"
        "Video Script:\n" + video_script + "\n\n"
        "Additional Information:\n" + additional_info + "\n\n"
        "Summary:"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=150
        )
        
        video_context = response.choices[0].message.content.strip()

        # pretty_details = json.dumps(video_context, indent=4, ensure_ascii=False)
        # logging.info(pretty_details)

        add_to_task_details("video_context", video_context)

        return video_context
    
    except Exception as e:
        logging.error("Error during ChatGPT API call: %s", e)
        return None
    
# ========================================================

def create_video_description (video_script, additional_info):
    prompt = (
        "Analyze the following information and create an moderately-sized engaging description for a YouTube video based on it.\n\n"
        "Video Script:\n" + video_script + "\n\n"
        "Additional Information:\n" + additional_info + "\n\n"
        "Summary:"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=150
        )
        
        video_description = response.choices[0].message.content.strip()

        # pretty_details = json.dumps(video_description, indent=4, ensure_ascii=False)
        # logging.info(pretty_details)

        add_to_task_details("video_description", video_description)

        return video_description
    
    except Exception as e:
        logging.error("Error during ChatGPT API call: %s", e)
        return None

# ========================================================

def get_video_query(video_script, additional_info):
    prompt = (
        "Analyze the following information and generate five accurate word or short phrase search queries that you would use "
        "to search for very similar and relevant videos on YouTube. Return the five queries as a JSON array. Each query should "
        "be concise and relevant to the content.\n\n"
        "Video Script:\n" + video_script + "\n\n"
        "Additional Information:\n" + additional_info + "\n\n"
        "JSON Array of 5 Queries:"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=150
        )
        
        video_queries_str = response.choices[0].message.content.strip()
        if video_queries_str.startswith("```"):
            video_queries_str = "\n".join(
                line for line in video_queries_str.splitlines() if not line.strip().startswith("```")
            )
        
        video_queries_str = video_queries_str.strip()
        video_queries = json.loads(video_queries_str)

        # pretty_details = json.dumps(video_queries, indent=4, ensure_ascii=False)
        # logging.info(pretty_details)
        
        add_to_task_details("video_queries", video_queries)
        
        aggregated_videos = []
        for query in video_queries:
            videos = youtube_search(query)
            if videos:
                aggregated_videos.extend(videos)
        
        aggregated_videos = aggregated_videos[:100]
        
        youtube_filter(aggregated_videos)
        
        return video_queries
    
    except Exception as e:
        logging.error("Error during ChatGPT API call: %s", e)
        return None