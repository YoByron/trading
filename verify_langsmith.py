import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from langsmith import Client

# Load environment variables
load_dotenv(override=True)

project_name = os.getenv("LANGCHAIN_PROJECT")
print(f"Targeting LangSmith Project: {project_name}")

client = Client()

try:
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("❌ CRITICAL: LANGCHAIN_API_KEY is missing from .env")
        # Don't exit, let's see if client picks it up from system headers or elsewhere?
        # Actually client() will look for it.

    # 1. Create the project explicitly (if it doesn't exist)
    print(f"Creating project {project_name} if missing...")
    if not client.has_project(project_name):
        client.create_project(project_name, description="Created via verification script")
        print(f"✅ Created project '{project_name}' in LangSmith")
    else:
        print(f"ℹ️  Project '{project_name}' already exists")

    # 2. Log a dummy run just to be sure it shows up in "Tracing Projects"
    # We can use the low-level API or just basic run creation
    print("Sending test trace...")

    run_id = uuid.uuid4()
    client.create_run(
        name="verification_trace",
        inputs={"input": "Hello LangSmith"},
        run_type="chain",
        project_name=project_name,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
    )
    print("✅ Test trace sent successfully")
    print(
        f"\n👉 Go to https://smith.langchain.com/o/{client.info.org_id}/projects/p/{client.read_project(project_name=project_name).id}"
    )

except Exception as e:
    print(f"❌ Failed to verify LangSmith: {e}")
