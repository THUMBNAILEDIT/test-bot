from openai import OpenAI
import logging
from config.config import OPENAI_API_KEY
from communication.task_details import delete_from_task_details, add_to_task_details
from research.check import check

client = OpenAI(api_key=OPENAI_API_KEY)

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
        
        add_to_task_details("video_context", video_context)

        return video_context
    
    except Exception as e:
        logging.error("Error during ChatGPT API call: %s", e)
        return None
    

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

        add_to_task_details("video_description", video_description)

        return video_description
    
    except Exception as e:
        logging.error("Error during ChatGPT API call: %s", e)
        return None
    

def get_video_query(video_script, additional_info):
    prompt = (
        "Analyze the following information and, separated by commas, list 5 key words and / or short phrases from it that could be used to search for similar or relevant information.\n\n"
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
        
        video_query = response.choices[0].message.content.strip()

        add_to_task_details("video_query", video_query)
        delete_from_task_details("video_script")
        delete_from_task_details("additional_info")

        check(video_query)

        return video_query
    
    except Exception as e:
        logging.error("Error during ChatGPT API call: %s", e)
        return None