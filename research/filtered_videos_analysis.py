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

def titles_analysis(filtered_videos):
    titles = [video["title"] for video in filtered_videos]
    video_context = get_task_details("video_context")
    thumbnail_packages = get_task_details("thumbnail_packages")

    analysis_prompt = (
        "You are a conversion copywriter specializing in viral YouTube titles. Study the 10 titles below and cluster them into exactly "
        f"{thumbnail_packages} distinct patterns based on shared linguistic or psychological hooks (e.g., curiosity‑gap, listicle, shock‑value, how‑to). "
        "For each pattern output an object {\"title_pattern\": \"<concise pattern description>\"} (max 12 words). "
        "Return the JSON array only.\n\n"
        "Video Titles:\n" + "\n".join(titles)
    )

    try:
        response = client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "You are a highly analytical assistant."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=1,
            max_completion_tokens=5000
        )

        raw_response = response.choices[0].message.content.strip()

        if raw_response.startswith("```"):
            raw_response = "\n".join([line for line in raw_response.splitlines() if not line.strip().startswith("```")]).strip()

        title_patterns = json.loads(raw_response)

        logging.info("")
        logging.info("")
        logging.info(f"Title patterns:\n{title_patterns}")
        logging.info("")
        logging.info("")


        generated_titles = []
        for pattern in title_patterns:
            prompt = (
                "You are a seasoned YouTube headline writer. Using the pattern below and the video context, craft ONE YouTube title ≤55 characters "
                "that maximizes curiosity and includes at least one high‑intent keyword from the context. Avoid clickbait clichés, keep sentence case. "
                "Return only the title.\n\n"
                f"Pattern:\n{pattern['title_pattern']}\n\n"
                f"Context:\n{video_context}"
            )

            title_response = client.chat.completions.create(
                model="o4-mini",
                messages=[
                    {"role": "system", "content": "You write compelling YouTube titles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1,
                max_completion_tokens=5000
            )

            generated_titles.append(title_response.choices[0].message.content.strip())

        final_deliverables = []
        for title in generated_titles:
            prompt = (
                "You are a YouTube growth copywriter. Write an optimized description (120‑200 words) that:\n"
                "- Opens with a 2‑line compelling hook that echoes the title\n"
                "- Summarizes the video value in 3‑5 concise bullets\n"
                "- Ends with a call‑to‑action to watch/subscribe\n"
                "- Seamlessly includes the main keywords from the context\n\n"
                f"Title:\n{title}\n\n"
                f"Context:\n{video_context}\n\n"
                "Return only the plain‑text description."
            )

            desc_response = client.chat.completions.create(
                model="o4-mini",
                messages=[
                    {"role": "system", "content": "You write effective YouTube descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1,
                max_completion_tokens=5000
            )

            description = desc_response.choices[0].message.content.strip()
            final_deliverables.append({
                "video_title": title,
                "video_description": description
            })

        add_to_task_details("final_deliverables", final_deliverables)
        return final_deliverables

    except Exception as e:
        logging.error("Error in title analysis workflow: %s", e)
        return None

def thumbnails_analysis(filtered_videos):
    client_wishes = get_task_details("additional_info")
    video_context = get_task_details("video_context")
    thumbnail_packages = get_task_details("thumbnail_packages")

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
        try:
            response = requests.post(analyze_url, headers=headers, params=params, json={"url": image_url})
            response.raise_for_status()
            result = response.json()

            captions = result.get("denseCaptionsResult", {}).get("values", [])
            seen = set()
            unique = [item["text"].strip() for item in captions if item["text"].strip() not in seen and not seen.add(item["text"].strip())]
            descriptions.append(" ".join(unique))
        except Exception as e:
            logging.error("Error processing thumbnail %s: %s", image_url, e)

        logging.info("")
        logging.info("")
        logging.info(f"Thumbnail descriptions:\n{json.dumps(descriptions, indent=4, ensure_ascii=False)}")
        logging.info("")
        logging.info("")

    try:
        prompt = (
            f"Analyze the following 10 thumbnail descriptions. Group them into exactly {thumbnail_packages} distinct visual patterns based on elements like colors, objects, number of people, layout, mood, etc.\n"
            "Return a JSON array of objects with a 'thumbnail_pattern' key describing each group. No other formatting.\n\n" +
            "\n".join(descriptions)
        )

        response = client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "You are an expert in visual pattern recognition for YouTube thumbnails."},
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            max_completion_tokens=5000
        )

        raw_response = response.choices[0].message.content.strip()

        if raw_response.startswith("```"):
            raw_response = "\n".join([line for line in raw_response.splitlines() if not line.strip().startswith("```")]).strip()

        thumbnail_patterns = json.loads(raw_response)

        logging.info("")
        logging.info("")
        logging.info(f"Thumbnail patterns:\n{json.dumps(thumbnail_patterns, indent=4, ensure_ascii=False)}")
        logging.info("")
        logging.info("")

        thumbnails_instructions = []
        for pattern in thumbnail_patterns:
            prompt = (
                "Based on the following thumbnail pattern, client's wishes, and video context, generate a concise, detailed prompt for an AI image generator.\n\n"
                f"Thumbnail Pattern:\n{pattern['thumbnail_pattern']}\n\n"
                f"Client's Wishes:\n{client_wishes}\n\n"
                f"Video Context:\n{video_context}\n\n"
                "Return only the prompt text, no formatting."
            )

            instr_response = client.chat.completions.create(
                model="o4-mini",
                messages=[
                    {"role": "system", "content": "You generate precise prompts for AI-based thumbnail generation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1,
                max_completion_tokens=5000
            )

            thumbnails_instructions.append(instr_response.choices[0].message.content.strip())

        logging.info("")
        logging.info("")
        logging.info(f"Thumbnail generation instructions:\n{json.dumps(thumbnails_instructions, indent=4, ensure_ascii=False)}")
        logging.info("")
        logging.info("")

        add_to_task_details("thumbnails_instructions", thumbnails_instructions)

        thumbnail_generation(thumbnails_instructions)
        
        return thumbnails_instructions

    except Exception as e:
        logging.error("Error during thumbnail analysis workflow: %s", e)
        return []