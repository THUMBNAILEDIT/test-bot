from openai import OpenAI
import json
import logging
from config.config import OPENAI_API_KEY
from communication.task_details import add_to_task_details
from research.youtube_search import youtube_search
from research.youtube_filter import youtube_filter

client = OpenAI(api_key=OPENAI_API_KEY)

# =================👇 Это функция, в которой мы генерируем контекст видео на основе сценария ==================

def get_video_context(video_script):
    prompt = (
        "You are a senior YouTube growth strategist. Summarize the script below in no more than 400 words, preserving all details that influence "
        "thumbnail, title and description performance.\n\n"
        "Use this exact structure:\n"
        "Hook:\n"
        "Main premise:\n"
        "Key moments:\n"
        "Viewer takeaway:\n"
        "Top keywords:\n\n"
        "Video Script:\n" + video_script + "\n\n"
        "Summary:"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
                
        video_context = response.choices[0].message.content.strip()

        logging.info("")
        logging.info("")
        logging.info(f"Video context:\n{json.dumps(video_context, indent=4, ensure_ascii=False)}")
        logging.info("")
        logging.info("")


        add_to_task_details("video_context", video_context)

        return video_context
    
    except Exception as e:
        logging.error("Error during ChatGPT API call: %s", e)
        return None

# =================👇 Это функция, в которой мы генерируем запросы на релевантные видео на основе сценария ==================

def get_video_query(video_script):
    prompt = (
        "You are a YouTube SEO analyst. From the script below, extract 5 concise search phrases (2–5 words) that viewers would type to find similar "
        "content. Each phrase must be broad enough to return at least one million results yet laser‑focused on the topic. "
        "Return ONLY a JSON array of strings.\n\n"
        "Video Script:\n" + video_script + "\n\n"
        "JSON Array:"
    )
    
    try:
        response = client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            max_completion_tokens=1000
        )
        
        video_queries_str = response.choices[0].message.content.strip()
        if video_queries_str.startswith("```"):
            video_queries_str = "\n".join(
                line for line in video_queries_str.splitlines() if not line.strip().startswith("```")
            )
        
        video_queries_str = video_queries_str.strip()
        video_queries = json.loads(video_queries_str)

        logging.info("")
        logging.info("")
        logging.info(f"Video queries:\n{json.dumps(video_queries, indent=4, ensure_ascii=False)}")
        logging.info("")
        logging.info("")
        
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