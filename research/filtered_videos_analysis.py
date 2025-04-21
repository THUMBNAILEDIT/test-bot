import json
import logging

import base64
import requests
import time

from openai import OpenAI, OpenAIError
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

        logging.info(f"Titles and descriptions:\n{json.dumps(final_deliverables, indent=4, ensure_ascii=False)}")

        add_to_task_details("final_deliverables", final_deliverables)
        return final_deliverables

    except Exception as e:
        logging.error("Error in title analysis workflow: %s", e)
        return None

def thumbnails_analysis(filtered_videos):
    client_wishes = get_task_details("additional_info")
    video_context = get_task_details("video_context")
    thumbnail_packages = get_task_details("thumbnail_packages")
    generated_titles = [t["video_title"] for t in get_task_details("final_deliverables")]

# ========================== 👇 СТАРЫЙ КОД FLORENCE 2.0 – НЕ УДАЛЯЙ НА ВСЯКИЙ СЛУЧАЙ, ОН НЕ АКТИВЕН =========================

    # api_version = "2024-02-01"
    # features = "denseCaptions"
    # analyze_url = f"{AZURE_VISION_ENDPOINT.rstrip('/')}/computervision/imageanalysis:analyze"

    # params = {
    #     "api-version": api_version,
    #     "features": features,
    #     "language": "en"
    # }

    # headers = {
    #     "Ocp-Apim-Subscription-Key": AZURE_VISION_KEY,
    #     "Content-Type": "application/json"
    # }

    # thumbnails = [video["thumbnail"] for video in filtered_videos]
    # descriptions = []

    # for image_url in thumbnails:
    #     try:
    #         response = requests.post(analyze_url, headers=headers, params=params, json={"url": image_url})
    #         response.raise_for_status()
    #         result = response.json()

    #         captions = result.get("denseCaptionsResult", {}).get("values", [])
    #         seen = set()
    #         unique = [item["text"].strip() for item in captions if item["text"].strip() not in seen and not seen.add(item["text"].strip())]
    #         descriptions.append(" ".join(unique))
    #     except Exception as e:
    #         logging.error("Error processing thumbnail %s: %s", image_url, e)

# ========================== 👇 ОДНА ИЗ ПРЕДЫДУЩИХ ВЕРСИЙ КОДА, ДАВАЛА 4-6 / 10 ОПИСАНИЙ =========================

    # thumbnails = [video["thumbnail"] for video in filtered_videos]
    # descriptions = []

    # for image_url in thumbnails:
    #     for attempt in range(5):
    #         try:
    #             prompt = (
    #                 "You are an expert in visual analysis for YouTube thumbnails. "
    #                 "Analyze the public image at the following URL. "
    #                 "Describe its content including people, objects, layout, mood, text, and colors. "
    #                 "This is a public image from YouTube and does not require authentication.\n\n"
    #                 f"Image URL: {image_url}"
    #             )

    #             time.sleep(2.0)

    #             response = client.chat.completions.create(
    #                 model="o4-mini",
    #                 messages=[
    #                     {"role": "system", "content": "You describe image content with precision and clarity."},
    #                     {"role": "user", "content": prompt}
    #                 ],
    #                 temperature=1,
    #                 max_completion_tokens=5000
    #             )

    #             content = response.choices[0].message.content.strip()
    #             if not content or "not able to" in content.lower():
    #                 descriptions.append("unavailable")
    #             else:
    #                 descriptions.append(content)
    #             break

    #         except OpenAIError as e:
    #             if "429" in str(e) or "rate limit" in str(e).lower():
    #                 wait = 2 ** attempt
    #                 logging.warning(f"Rate limit hit. Retry #{attempt + 1} in {wait}s")
    #                 time.sleep(wait)
    #             else:
    #                 logging.error(f"Error processing thumbnail {image_url}: {e}")
    #                 descriptions.append("unavailable")
    #                 break
    #         except Exception as e:
    #             logging.error(f"Error processing thumbnail {image_url}: {e}")
    #             descriptions.append("unavailable")
    #             break

# ========================== 👇 ТЕКУЩАЯ ВЕРСИЯ КОДА, ДАВАЛА МНЕ 9 / 10 ОПИСАНИЙ =========================

    thumbnails = [video["thumbnail"] for video in filtered_videos]
    descriptions = []

    def is_refusal(text: str) -> bool:
        lowered = text.lower()
        return (
            "i’m sorry" in lowered or
            "i do not" in lowered or
            "i can't" in lowered or
            "not able to" in lowered or
            "unable to" in lowered
        )

    for image_url in thumbnails:
        for attempt in range(5):
            try:
                if attempt == 0:
                    prompt = (
                        "You are a YouTube thumbnail analyst. Below is a description of a scene, provided as a public reference. "
                        "Describe what this scene likely looks like: composition, objects, people, layout, colors, text, and visual tone.\n\n"
                        f"Scene reference: {image_url}"
                    )
                    system_prompt = "You analyze visual compositions based on descriptions or public references. You never ask for image uploads."
                else:
                    prompt = (
                        "You are an expert in analyzing YouTube thumbnails. "
                        "The image is publicly accessible and hosted on YouTube’s CDN. "
                        "Describe the content of the image at this URL, including people, objects, colors, layout, text, and overall visual tone.\n\n"
                        f"Image URL: {image_url}"
                    )
                    system_prompt = "You describe image content with visual clarity and precision."

                time.sleep(2.0)

                response = client.chat.completions.create(
                    model="o4-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=1,
                    max_completion_tokens=5000
                )

                content = response.choices[0].message.content.strip()
                if not content or is_refusal(content):
                    if attempt < 4:
                        logging.warning(f"Refusal detected for {image_url}. Retrying with alternate prompt (attempt {attempt + 2})...")
                        continue
                    else:
                        descriptions.append("unavailable")
                else:
                    descriptions.append(content)
                break

            except OpenAIError as e:
                if "429" in str(e) or "rate limit" in str(e).lower():
                    wait = 2 ** attempt
                    logging.warning(f"Rate limit hit. Retry #{attempt + 1} in {wait}s")
                    time.sleep(wait)
                else:
                    logging.error(f"OpenAI error for thumbnail {image_url}: {e}")
                    descriptions.append("unavailable")
                    break
            except Exception as e:
                logging.error(f"General error for thumbnail {image_url}: {e}")
                descriptions.append("unavailable")
                break

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
        for i, pattern in enumerate(thumbnail_patterns):
            prompt = (
                "Based on the following thumbnail pattern, video title, client's wishes, and video context, "
                "generate a concise, detailed prompt for an AI image generator.\n\n"
                f"Thumbnail Pattern:\n{pattern['thumbnail_pattern']}\n\n"
                f"Video Title:\n{generated_titles[i]}\n\n"
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
            
            logging.info(f"Generated title in use:\n{json.dumps(generated_titles[i], indent=4, ensure_ascii=False)}")
            logging.info(f"Pattern in use:\n{json.dumps(pattern, indent=4, ensure_ascii=False)}")

            thumbnails_instructions.append(instr_response.choices[0].message.content.strip())

        logging.info("")
        logging.info("")
        logging.info(f"Thumbnail generation instructions:\n{json.dumps(thumbnails_instructions, indent=4, ensure_ascii=False)}")
        logging.info("")
        logging.info("")

        add_to_task_details("thumbnails_instructions", thumbnails_instructions)

        # thumbnail_generation(thumbnails_instructions) – ТУТ Я ПЕРЕКРЫЛ РАБОТУ FLUX ПО ПРИЧИНЕ ПРЕВЫШЕНИЯ ЛИМИТА
        
        return thumbnails_instructions

    except Exception as e:
        logging.error("Error during thumbnail analysis workflow: %s", e)
        return []