import json
import logging
from openai import OpenAI
from config.config import OPENAI_API_KEY
from communication.task_details import get_task_details, add_to_task_details

client = OpenAI(api_key=OPENAI_API_KEY)

def filtered_videos_analysis(filtered_videos):
    titles = [video["title"] for video in filtered_videos]
    
    video_context = get_task_details("video_context")
    thumbnail_packages = get_task_details("thumbnail_packages")
    
    prompt = (
        "Analyze the following 10 YouTube video titles and provide a serious comparative analysis on their tone, "
        "common words, and stylistic elements. Then, using the provided video context, generate {N} new, engaging YouTube "
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
        
        generated_titles = response.choices[0].message.content.strip()
        
        if generated_titles.startswith("```"):
            lines = generated_titles.splitlines()
            cleaned_lines = [line for line in lines if not line.strip().startswith("```")]
            generated_titles = "\n".join(cleaned_lines).strip()
        
        try:
            titles_array = json.loads(generated_titles)
            cleaned_generated_titles = json.dumps(titles_array, separators=(',',':'), ensure_ascii=False)
        except Exception as e:
            logging.error("Error cleaning generated titles JSON: %s", e)
            cleaned_generated_titles = generated_titles
        
        add_to_task_details("generated_titles", cleaned_generated_titles)
        
        logging.info("Task details: %s", get_task_details())
        
        return cleaned_generated_titles
        
    except Exception as e:
        logging.error("Error during ChatGPT API call for title generation: %s", e)
        return None