import json
import logging
import requests
from openai import OpenAI
from config.config import OPENAI_API_KEY, AZURE_VISION_KEY, AZURE_VISION_ENDPOINT
from communication.task_details import get_task_details, add_to_task_details
from generation.thumbnails_generation import thumbnail_generation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)








# =================👇 Это функция, в которой мы анализируем названия 10-ти отобранных видео ==================

def titles_analysis(filtered_videos):
    titles = [video["title"] for video in filtered_videos]
    video_context = get_task_details("video_context")
    thumbnail_packages = get_task_details("thumbnail_packages")

    analysis_prompt = (
        "Analyze the following 10 YouTube video titles. Identify common themes, tone, frequently used words, and names. "
        "Describe the stylistic and emotional elements they share. Your answer should be short and precise.\n\n"
        "Video Titles:\n" + "\n".join(titles)
    )

    try:
        analysis_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a highly analytical assistant."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.4,
            max_tokens=250
        )

        analysis_summary = analysis_response.choices[0].message.content.strip()

# ======================================================================================= Тут мы выводим результат в терминал
        logging.info(f"Titles analysis results:\n{json.dumps(analysis_summary, indent=4, ensure_ascii=False)}")
# =======================================================================================

        generation_prompt = (
            "Based on the following analysis and the given video context, generate {N} new YouTube video titles. "
            "Make sure each title is relevant, engaging, and stylistically aligned with the analyzed titles. "
            "Return only a raw JSON array with the titles, no other formatting.\n\n"
            "Analysis:\n{summary}\n\n"
            "Video Context:\n{context}".format(
                N=thumbnail_packages,
                summary=analysis_summary,
                context=video_context
            )
        )

        generation_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You generate high-performing YouTube titles based on deep analysis."},
                {"role": "user", "content": generation_prompt}
            ],
            temperature=0.6,
            max_tokens=200
        )

        titles = generation_response.choices[0].message.content.strip()

        if titles.startswith("```"):
            lines = titles.splitlines()
            cleaned_lines = [line for line in lines if not line.strip().startswith("```")]
            titles = "\n".join(cleaned_lines).strip()

        try:
            titles_array = json.loads(titles)
            cleaned_titles = json.dumps(titles_array, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:
            logging.error("Error cleaning generated titles JSON: %s", e)
            cleaned_titles = titles

        generated_titles = cleaned_titles

# ======================================================================================= Тут мы выводим результат в терминал
        logging.info(f"Generated titles:\n{json.dumps(generated_titles, indent=4, ensure_ascii=False)}")
# =======================================================================================

        add_to_task_details("generated_titles", generated_titles)

        return generated_titles

    except Exception as e:
        logging.error("Error during ChatGPT API call for title analysis/generation: %s", e)
        return None
    







# =================👇 Это функция, в которой мы анализируем превью 10-ти отобранных видео ==================

def thumbnails_analysis(filtered_videos):
    client_wishes = get_task_details("additional_info")

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
    
    video_context = get_task_details("video_context")

    try:
        analysis_prompt = (
            "You are an expert at analyzing visual cues from YouTube thumbnails. "
            "Review the following 10 thumbnail descriptions and summarize common visual elements, recurring styles, colors, tone, and key motifs.\n\n"
            + "\n".join(descriptions)
        )

        analysis_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert visual analyst for YouTube thumbnails."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.4,
            max_tokens=300
        )

        visual_summary = analysis_response.choices[0].message.content.strip()

# ======================================================================================= Тут мы выводим результат в терминал
        logging.info(f"Thumbnail analysis results:\n{json.dumps(visual_summary, indent=4, ensure_ascii=False)}")
# =======================================================================================

        generation_prompt = (
            "Based on the following analysis of 10 successful YouTube thumbnails, the provided video context and the client's wishes, "
            "generate a short and precise prompt for an AI image generator. "
            "The goal is to create a high-performing thumbnail that visually fits the niche and reflects the video's idea clearly.\n\n"
            f"Thumbnail Analysis:\n{visual_summary}\n\n"
            f"Client's wishes:\n{client_wishes}\n\n"
            f"Video Context:\n{video_context}"
        )

        generation_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You generate prompts for AI-based thumbnail generators."},
                {"role": "user", "content": generation_prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )

        thumbnail_instruction = generation_response.choices[0].message.content.strip()

# ======================================================================================= Тут мы выводим результат в терминал
        logging.info(f"Thumbnail instruction:\n{json.dumps(thumbnail_instruction, indent=4, ensure_ascii=False)}")
# =======================================================================================

    except Exception as e:
        logging.error("Error generating image preview instruction: %s", e)
        return []

    thumbnail_generation(thumbnail_instruction)
    return descriptions