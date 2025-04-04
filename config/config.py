import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_API_URL = os.getenv("SLACK_API_URL")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
ASANA_ACCESS_TOKEN = os.getenv("ASANA_ACCESS_TOKEN")
ASANA_PROJECT_ID = os.getenv("ASANA_PROJECT_ID")
ASANA_ARCHIVE_PROJECT_ID = os.getenv("ASANA_ARCHIVE_PROJECT_ID")
ASANA_WORKSPACE_ID = os.getenv("ASANA_WORKSPACE_ID")
ASANA_ADMIN_ID = os.getenv("ASANA_ADMIN_ID")
ASANA_WEBHOOK_URL = os.getenv("ASANA_WEBHOOK_URL")
MONOBANK_API_KEY = os.getenv("MONOBANK_API_KEY")
MONOBANK_API_BASEURL = os.getenv("MONOBANK_API_BASEURL")
BACKEND_BASEURL = os.getenv("BACKEND_BASEURL")
GOOGLE_DOCS_CREDENTIALS = os.environ["GOOGLE_DOCS_CREDENTIALS"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
YOUTUBE_DATA_API_KEY = os.environ["YOUTUBE_DATA_API_KEY"]