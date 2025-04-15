import json
import logging
import replicate
from openai import OpenAI
import logging
import re
from config.config import OPENAI_API_KEY
from communication.task_details import get_task_details, add_to_task_details, delete_from_task_details
from communication.asana_utils import post_comment_to_task
from database.database import update_deliverables

client = OpenAI(api_key=OPENAI_API_KEY)

def format_final_deliverables(final_deliverables):
    lines = ["🎁 FINAL_OUTPUT_START"]

    for i, package in enumerate(final_deliverables.values(), 1):
        lines.append(f"*Package {i}* \n\n")
        lines.append(f"*Title:* {package['video_title']} \n\n")
        lines.append(f"*Description:* {package['video_description']} \n\n")
        lines.append(f"*Thumbnail:* {package['video_thumbnail']} \n\n")
        lines.append("\n\n")

    lines.append("🎁 FINAL_OUTPUT_END")
    return "\n".join(lines)

def format_revision_results(revised_packages):
    lines = ["🎁 FINAL_OUTPUT_START", "*🔁 Revised Thumbnails:*", ""]

    for key, package in revised_packages.items():
        lines.append(f"*{key.replace('_', ' ').title()}*")
        lines.append(f"*Your request:* {package['prompt']}")
        lines.append(f"*The thumbnail we revised:* {package['original_thumbnail']}")
        lines.append(f"*The updated thumbnail:* {package['revised_thumbnail']}")
        lines.append("")

    lines.append("🎁 FINAL_OUTPUT_END")
    return "\n".join(lines)

def thumbnail_generation(thumbnail_instruction):
    thumbnail_packages = int(get_task_details("thumbnail_packages"))

    generated_titles_raw = get_task_details("generated_titles")
    generated_titles = json.loads(generated_titles_raw) if isinstance(generated_titles_raw, str) else generated_titles

    video_description = get_task_details("video_description")
    generated_thumbnails = []

    try:
        input_data = {
            "prompt": thumbnail_instruction,
            "prompt_upsampling": True,
            "width": 1280,
            "height": 720,
            "output_quality": 80,
            "output_format": "jpg",
            "aspect_ratio": "custom",
            "safety_tolerance": 4
        }

        for _ in range(thumbnail_packages):
            output = replicate.run("black-forest-labs/flux-1.1-pro", input=input_data)
            
            image_url = str(output[0]) if isinstance(output, list) else str(output)
            generated_thumbnails.append(image_url)
            
        final_deliverables = {}
        for i in range(thumbnail_packages):
            final_deliverables[f"package_{i+1}"] = {
                "video_title": generated_titles[i],
                "video_description": video_description,
                "video_thumbnail": generated_thumbnails[i]
            }

        add_to_task_details("final_deliverables", final_deliverables)
        delete_from_task_details("video_script")
        delete_from_task_details("additional_info")
        delete_from_task_details("video_context")
        delete_from_task_details("video_description")
        delete_from_task_details("thumbnail_packages")
        delete_from_task_details("video_queries")
        delete_from_task_details("generated_titles")

        logging.info(json.dumps(get_task_details(), indent=4, ensure_ascii=False))
        update_deliverables(get_task_details())

        task_id = get_task_details("task_id")
        comment_text = format_final_deliverables(final_deliverables)
        post_comment_to_task(task_id, comment_text)

        return final_deliverables
    
    except Exception as e:
        logging.error("Error in thumbnail generation: %s", e)
        return []

def thumbnail_revision(task_id, user_message, full_data):
    try:
        system_prompt = (
            "You are an assistant in an AI-based thumbnail generation service. "
            "A client has submitted a revision request in free-text format. Your tasks are:\n\n"
            "1. Analyze the revision message carefully.\n"
            "2. Clearly identify how many thumbnails (packages) the message refers to, and specify their numbers.\n"
            "3. Precisely match each instruction in the message to the correct package using keywords like 'first', 'second', 'package 1', 'thumbnail 3', etc. "
            "If there's only one package in the provided data, explicit reference isn't required.\n"
            "4. Determine if the client is referring to the original thumbnail ('video_thumbnail') or a specific revised thumbnail "
            "within 'revised_thumbnails' (if revisions are available). If unclear, default to the latest available revision or the original thumbnail if no revisions exist.\n"
            "5. Extract a concise and clear prompt suitable for AI-based thumbnail generation from each instruction.\n"
            "6. Include the correct thumbnail URL corresponding to the identified package and revision.\n\n"
            "If the revision message is unclear about which thumbnail it refers to (except when there's only one thumbnail available) or doesn't contain sufficient details for generating a prompt, respond explicitly with:\n"
            "{ \"error\": \"description of the problem\" }\n\n"
            "Always respond strictly in the following JSON array format:\n"
            "[\n"
            "  {\n"
            "    \"package_number\": 1,\n"
            "    \"prompt\": \"Make the background darker and add a red border\",\n"
            "    \"original_thumbnail\": \"https://example.com/image1.jpg\"\n"
            "  }\n"
            "]"
        )

        user_prompt = f"""
Here is the client's revision message:
\"\"\"
{user_message}
\"\"\"

Here is the thumbnail object:
{json.dumps(full_data, ensure_ascii=False)}

Return a JSON array in the following format:
[
  {{
    "package_number": <number>,
    "prompt": <short prompt for the AI>,
    "original_thumbnail": <URL>
  }}
]

OR, if the message is unclear, return:
{{ "error": "description of the problem" }}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content

        json_match = re.search(r'(\[\s*\{.*\}\s*\])', content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(1))
        else:
            logging.error("No valid JSON found in response.")
            post_comment_to_task(
                task_id,
                "🎁 FINAL_OUTPUT_START\n⚠️ Sorry, we couldn't understand your revision request. "
                "Please try again using clear and specific instructions.\n🎁 FINAL_OUTPUT_END"
            )
            return

        logging.info("AI parsed response:")
        logging.info(parsed)

        if isinstance(parsed, dict) and parsed.get("error"):
            logging.warning(f"Revision message unclear: {parsed['error']}")
            post_comment_to_task(
                task_id,
                f"🎁 FINAL_OUTPUT_START\n⚠️ {parsed['error']}\n🎁 FINAL_OUTPUT_END"
            )
            return

        revised_packages = {}
        task_deliverables = full_data["final_deliverables"]

        for item in parsed:
            package_number = item["package_number"]
            package_key = f"package_{package_number}"
            prompt = item["prompt"]

            package = task_deliverables.get(package_key, {})
            revised_thumbnails = package.get("revised_thumbnails", [])

            original_url = revised_thumbnails[-1] if revised_thumbnails else package.get("video_thumbnail")

            input_data = {
                "prompt": prompt,
                "image": original_url,
                "width": 1280,
                "height": 720,
                "output_format": "jpg",
                "prompt_upsampling": True,
                "output_quality": 80,
                "aspect_ratio": "custom",
                "safety_tolerance": 4
            }

            output = replicate.run("black-forest-labs/flux-1.1-pro", input=input_data)
            new_url = str(output[0]) if isinstance(output, list) else str(output)

            revised_thumbnails.append(new_url)
            package["revised_thumbnails"] = revised_thumbnails
            task_deliverables[package_key] = package

            revised_packages[package_key] = {
                "prompt": prompt,
                "original_thumbnail": original_url,
                "revised_thumbnail": new_url
            }

        full_data["final_deliverables"] = task_deliverables
        update_deliverables(full_data)

        comment = format_revision_results(revised_packages)
        post_comment_to_task(task_id, comment)

    except Exception as e:
        logging.error(f"Error in thumbnail_revision: {e}")
        post_comment_to_task(
            task_id,
            "🎁 FINAL_OUTPUT_START\n⚠️ Something went wrong while processing your revision request.\n🎁 FINAL_OUTPUT_END"
        )