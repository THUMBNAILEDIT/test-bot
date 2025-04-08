from supabase import create_client, Client
from config.config import SUPABASE_URL, SUPABASE_KEY

# ========================================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================================================

def fetch_client_data(channel_id: str):
    response = supabase.table("clientbase").select("*").eq("slack_id", channel_id).execute()
    return response.data[0] if response.data else None

# ========================================================

def fetch_client_data_by_task_id(task_id: str):
    response = supabase.table("clientbase").select("*").like("current_tasks", f"%{task_id}%").execute()
    return response.data[0] if response.data else None

# ========================================================

def update_client_credits(channel_id: str, new_credits: int):
    supabase.table("clientbase").update({"current_credits": new_credits}).eq("slack_id", channel_id).execute()

# ========================================================

def update_client_current_tasks(channel_id: str, task_id: str):
    client = fetch_client_data(channel_id)
    if client:
        current_tasks = client.get("current_tasks", "")
        tasks_list = current_tasks.split(",") if current_tasks else []
        tasks_list.append(task_id)
        updated_tasks = ",".join(tasks_list)
        supabase.table("clientbase").update({"current_tasks": updated_tasks}).eq("slack_id", channel_id).execute()

# ========================================================

def remove_task_from_current_tasks(channel_id: str, task_id: str):
    client = fetch_client_data(channel_id)
    if client:
        current_tasks = client.get("current_tasks", "")
        tasks_list = current_tasks.split(",") if current_tasks else []
        if task_id in tasks_list:
            tasks_list.remove(task_id)
        updated_tasks = ",".join(tasks_list)
        supabase.table("clientbase").update({"current_tasks": updated_tasks}).eq("slack_id", channel_id).execute()

# ========================================================

def update_client_thread_mapping(channel_id: str, thread_ts: str, task_id: str):
    client = fetch_client_data(channel_id)
    if client:
        current_mappings = client.get("thread_mappings", {}) or {}
        current_mappings[thread_ts] = task_id
        supabase.table("clientbase").update({"thread_mappings": current_mappings}).eq("slack_id", channel_id).execute()

# ========================================================

def remove_thread_mappings_for_task(channel_id: str, task_id: str):
    client = fetch_client_data(channel_id)
    if client:
        thread_mappings = client.get("thread_mappings", {})
        updated_mappings = {ts: tid for ts, tid in thread_mappings.items() if tid != task_id}
        supabase.table("clientbase").update({"thread_mappings": updated_mappings}).eq("slack_id", channel_id).execute()

# ========================================================

def update_task_history(channel_id: str, task_id: str):
    client = fetch_client_data(channel_id)
    if client:
        task_history = client.get("task_history", "")
        history_list = task_history.split(",") if task_history else []
        
        history_list.append(task_id)
        if len(history_list) > 10:
            history_list.pop(0)
        
        updated_history = ",".join(history_list)
        supabase.table("clientbase").update({"task_history": updated_history}).eq("slack_id", channel_id).execute()

# ========================================================

def get_access_token(client_id: str):
    response = supabase.table("clientbase").select("access_token").eq("slack_id", client_id).execute()

    if response.data and response.data[0].get("access_token"):
        return response.data[0]["access_token"]
    else:
        raise ValueError(f"AccessToken not found for client_id: {client_id}")
    
# ========================================================

def activate_client_subscription(channel_id: str):
    supabase.table("clientbase").update({"is_subscription_active": True}).eq("slack_id", channel_id).execute()

# ========================================================

def get_deliverables_by_task_id(channel_id: str, task_id: str):
    client = fetch_client_data(channel_id)
    if client:
        deliverables = client.get("deliverables", {})
        return deliverables.get(task_id)
    return None

# ========================================================

def update_deliverables(data: dict):
    channel_id = data.get("channel_id")
    task_id = data.get("task_id")

    if not channel_id or not task_id:
        raise ValueError("Missing channel_id or task_id in data")

    client = fetch_client_data(channel_id)
    if client:
        current_deliverables = client.get("deliverables", {}) or {}
        current_deliverables[task_id] = data
        supabase.table("clientbase").update({"deliverables": current_deliverables}).eq("slack_id", channel_id).execute()