task_details = {}

# ========================================================

def create_task_details(channel_id, task_id, video_link, additional_info, thumbnail_packages):
    global task_details
    task_details = {
        "channel_id": channel_id,
        "task_id": task_id,
        "video_link": video_link,
        "additional_info": additional_info,
        "thumbnail_packages": thumbnail_packages
    }
    return task_details

# ========================================================

def add_to_task_details(key, value):
    global task_details
    task_details[key] = value

# ========================================================

def delete_from_task_details(key):
    global task_details
    if key in task_details:
        del task_details[key]

# ========================================================

def get_task_details(key=None):
    if key:
        return task_details.get(key)
    return task_details