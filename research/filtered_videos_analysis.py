import json
import logging
import requests
from openai import OpenAI
from config.config import OPENAI_API_KEY, AZURE_VISION_KEY, AZURE_VISION_ENDPOINT
from communication.task_details import get_task_details, add_to_task_details
from generation.thumbnails_generation import thumbnail_generation

# ========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

# ========================================================

def titles_analysis(filtered_videos):
    titles = [video["title"] for video in filtered_videos]
    
    video_context = get_task_details("video_context")
    thumbnail_packages = get_task_details("thumbnail_packages")
    
    prompt = (
        "Analyze the following 10 YouTube video titles and provide a serious comparative analysis on their tone, "
        "common words, frequently mentioned names and stylistic elements. Then, using the provided video context, generate {N} new, engaging YouTube "
        "video titles that best reflect the content and tone. Output your answer as a JSON array containing only the titles, "
        "with no additional keys or formatting.\n\n"
        "Video Titles:\n{titles}\n\n"
        "Video Context:\n{context}\n\n"
        "Number of titles to generate: {N}".format(
            N=thumbnail_packages,
            titles="\n".join(titles),
            context=video_context
        )
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a highly analytical assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )
        
        titles = response.choices[0].message.content.strip()
        
        if titles.startswith("```"):
            lines = titles.splitlines()
            cleaned_lines = [line for line in lines if not line.strip().startswith("```")]
            titles = "\n".join(cleaned_lines).strip()
        
        try:
            titles_array = json.loads(titles)
            cleaned_titles = json.dumps(titles_array, separators=(',',':'), ensure_ascii=False)
        except Exception as e:
            logging.error("Error cleaning generated titles JSON: %s", e)
            cleaned_titles = titles
        
        generated_titles = cleaned_titles
        add_to_task_details("generated_titles", generated_titles)

        # logging.info(json.dumps(generated__titles, indent=4, ensure_ascii=False))

        return generated_titles
    
    except Exception as e:
        logging.error("Error during ChatGPT API call for title generation: %s", e)
        return None

# ========================================================

def thumbnails_analysis(filtered_videos):
    api_version = "2024-02-01"
    features = "denseCaptions"
    analyze_url = f"{AZURE_VISION_ENDPOINT.rstrip('/')}/computervision/imageanalysis:analyze"
    
    params = {
        "api-version": api_version,
        "features": features,
        "language": "en"
    }
    
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_VISION_KEY,
        "Content-Type": "application/json"
    }
    
    thumbnails = [video["thumbnail"] for video in filtered_videos]
    # logging.info(json.dumps(thumbnails, indent=4, ensure_ascii=False))
    
    descriptions = []
    
    for image_url in thumbnails:
        data = {"url": image_url}
        try:
            response = requests.post(analyze_url, headers=headers, params=params, json=data)
            response.raise_for_status()
            result = response.json()
            
            captions_list = result.get("denseCaptionsResult", {}).get("values", [])
            unique_captions = []
            seen = set()
            for item in captions_list:
                text = item.get("text", "").strip()
                if text and text not in seen:
                    seen.add(text)
                    unique_captions.append(text)
                    
            full_description = " ".join(unique_captions)
            descriptions.append(full_description)
            
        except requests.RequestException as e:
            logging.error("Request error for %s: %s", image_url, e)
        except Exception as e:
            logging.error("Unexpected error for %s: %s", image_url, e)
    
    # logging.info(json.dumps(descriptions, indent=4, ensure_ascii=False))

    video_context = get_task_details("video_context")
    # thumbnail_packages = get_task_details("thumbnail_packages")

    try:
        prompt = (
        "Analyze the following 10 YouTube video thumbnail descriptions:\n\n" +
        "\n".join(descriptions) +
        "\n\nVideo Context:\n" +
        video_context +
        "\n\nBased the video context and the description of these 10 thumbnails, generate a very short, concise and accurate prompt "
        "for an AI image generator so it can create an ideal YouTube thumbnail capturing the essence of the video's content."
    )
        
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at creating detailed prompts for AI YouTube thumbnail generation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )
        
        thumbnail_instruction = chat_response.choices[0].message.content.strip()
        # logging.info("Generated Instruction Prompt: %s", thumbnail_instruction)
    except Exception as e:
        logging.error("Error generating image preview instruction: %s", e)

    thumbnail_generation(thumbnail_instruction)

    return descriptions