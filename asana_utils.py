import requests
from config import ASANA_ACCESS_TOKEN, ASANA_PROJECT_ID, ASANA_ARCHIVE_PROJECT_ID, ASANA_WEBHOOK_URL

if not ASANA_WEBHOOK_URL:
    raise ValueError("ASANA_WEBHOOK_URL environment variable is not set!")

def register_webhook_for_task(task_id):
    url = "https://app.asana.com/api/1.0/webhooks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "data": {
            "resource": task_id,
            "target": ASANA_WEBHOOK_URL
        }
    }
    requests.post(url, headers=headers, json=data)

def create_asana_task(task_name, task_notes):
    url = "https://app.asana.com/api/1.0/tasks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}"
    }
    data = {
        "data": {
            "name": task_name,
            "notes": task_notes,
            "projects": [ASANA_PROJECT_ID]
        }
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        task_id = response.json().get("data", {}).get("gid")
        return task_id
    else:
        print(f"Failed to create task: {response.text}")
        return None

def move_task_to_archive(task_id):
    if not ASANA_ARCHIVE_PROJECT_ID:
        print("Error: Archive project ID is missing.")
        return
        
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}/projects"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        current_projects = response.json().get("data", [])
        
        for project in current_projects:
            if project["gid"] != ASANA_ARCHIVE_PROJECT_ID:
                remove_url = f"https://app.asana.com/api/1.0/tasks/{task_id}/removeProject"
                data = {
                    "data": {
                        "project": project["gid"]
                    }
                }
                requests.post(remove_url, headers=headers, json=data)

        add_url = f"https://app.asana.com/api/1.0/tasks/{task_id}/addProject"
        data = {
            "data": {
                "project": ASANA_ARCHIVE_PROJECT_ID
            }
        }
        add_response = requests.post(add_url, headers=headers, json=data)
        
        if add_response.status_code != 200:
            print(f"Failed to move task {task_id} to archive: {add_response.text}")
        elif response.status_code != 200:
            print(f"Failed to fetch current projects for task {task_id}: {response.text}")

def create_asana_subtask(parent_task_id, subtask_name, subtask_notes):
    """
    Creates a subtask under the given parent task ID in Asana.
    parent_task_id: The main task's ID (string).
    subtask_name: The name/title of the subtask (string).
    subtask_notes: The description or notes for the subtask (string).
    Returns: The ID of the newly created subtask, or None if creation failed.
    """
    url = f"https://app.asana.com/api/1.0/tasks/{parent_task_id}/subtasks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}"
    }
    data = {
        "data": {
            "name": subtask_name,
            "notes": subtask_notes
            # You can also add "projects": [ASANA_PROJECT_ID] if you want the subtask to appear in a project.
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        subtask_id = response.json().get("data", {}).get("gid")
        return subtask_id
    else:
        print(f"Failed to create subtask: {response.text}")
        return None