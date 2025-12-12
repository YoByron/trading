#!/usr/bin/env python3
"""
Setup AI Infrastructure

Automates the provisioning of:
1. Google Cloud Project & APIs (Dialogflow, Vertex AI)
2. Dialogflow CX Agent
3. LangSmith Configuration (updates .env)

Usage:
    python3 scripts/setup_ai_infrastructure.py
"""

import os
import subprocess
import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

REQUIRED_APIS = [
    "dialogflow.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
]


def run_command(command, shell=False):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error output: {e.stderr}")
        raise


def check_gcloud_auth():
    """Check if gcloud is authenticated."""
    try:
        account = run_command(["gcloud", "config", "get-value", "account"])
        logger.info(f"Authenticated as: {account}")
        return True
    except Exception:
        logger.error("gcloud not authenticated. Please run `gcloud auth login` first.")
        return False


def setup_gcp_project(project_id):
    """Setup Google Cloud Project."""
    logger.info(f"Setting up GCP Project: {project_id}")

    # Check if project exists, create if not (handling permissions might be tricky, assuming existing or user creates)
    # For now, we assume user provides a project ID they want to use/create.

    # Set project
    run_command(["gcloud", "config", "set", "project", project_id])

    # Enable APIs
    logger.info("Enabling required APIs...")
    for api in REQUIRED_APIS:
        try:
            logger.info(f"Enabling {api}...")
            run_command(["gcloud", "services", "enable", api])
        except Exception as e:
            logger.warning(f"Failed to enable {api}: {e}")
            if api == "dialogflow.googleapis.com":  # Critical
                raise

    logger.info("APIs enabled successfully (or skipped non-critical).")


def create_dialogflow_agent(project_id, display_name="TradingAssistant"):
    """Create a Dialogflow CX Agent."""
    logger.info(f"Creating Dialogflow CX Agent: {display_name}")

    try:
        from google.api_core.client_options import ClientOptions
        from google.cloud import dialogflowcx_v3 as dialogflow
    except ImportError:
        logger.error(
            "google-cloud-dialogflow-cx not installed. Run `pip install google-cloud-dialogflow-cx`"
        )
        return None

    # Use global location
    location = "global"
    parent = f"projects/{project_id}/locations/{location}"

    client_options = ClientOptions(api_endpoint=f"{location}-dialogflow.googleapis.com:443")
    agents_client = dialogflow.AgentsClient(client_options=client_options)

    agent = dialogflow.Agent(
        display_name=display_name,
        default_language_code="en",
        time_zone="America/New_York",
        description="AI Trading Assistant for Portfolio Management",
    )

    try:
        response = agents_client.create_agent(parent=parent, agent=agent)
        logger.info(f"Agent created: {response.name}")
        # Format: projects/*/locations/*/agents/*
        agent_id = response.name.split("/")[-1]
        return agent_id
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        return None


def update_env_file(project_id, agent_id, langchain_project):
    """Update .env file with new configurations."""
    env_path = Path(".env")
    if not env_path.exists():
        logger.error(".env file not found!")
        return

    logger.info("Updating .env file...")
    lines = env_path.read_text().splitlines()
    new_lines = []

    updates = {
        "GOOGLE_CLOUD_PROJECT": project_id,
        "DIALOGFLOW_PROJECT_ID": project_id,
        "DIALOGFLOW_AGENT_ID": agent_id,
        "LANGCHAIN_PROJECT": langchain_project,
        "LANGCHAIN_TRACING_V2": "true",
    }

    # Track which keys we've updated
    updated_keys = set()

    for line in lines:
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Add missing keys
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}")

    env_path.write_text("\n".join(new_lines) + "\n")
    logger.info(".env updated successfully.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Setup AI Infrastructure")
    parser.add_argument("--project-id", help="Google Cloud Project ID")
    parser.add_argument(
        "--create-project", action="store_true", help="Create the project if it doesn't exist"
    )
    parser.add_argument("--langsmith-project", help="LangSmith Project Name")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    args = parser.parse_args()

    print("DEBUG: Starting setup script...")
    if not check_gcloud_auth():
        print("DEBUG: Auth failed")
        sys.exit(1)

    print("\n🤖 Unified AI Infrastructure Setup 🤖\n")

    # 1. Project Setup
    if args.project_id:
        project_id = args.project_id
    else:
        default_proj = f"trading-ai-{uuid.uuid4().hex[:6]}"
        project_id = (
            input(f"Enter Google Cloud Project ID (default: {default_proj}): ").strip()
            or default_proj
        )

    print(f"\nTargeting Project: {project_id}")

    if not args.yes:
        confirm = input("Create/Configure this project? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)

    try:
        # Create project if requested
        if args.create_project:
            logger.info(f"Creating project {project_id}...")
            # Attempt creation - might fail if ID exists or no billing
            try:
                run_command(["gcloud", "projects", "create", project_id])
                print(f"✅ Created project {project_id}")
            except Exception as e:
                print(f"⚠️  Could not create project (might already exist): {e}")

        print("\nConfiguring GCP Project...")
        setup_gcp_project(project_id)

        # 2. Dialogflow Setup
        print("\nSetting up Dialogflow CX...")
        agent_id = create_dialogflow_agent(project_id)
        if not agent_id:
            print("Failed to create Dialogflow Agent. Check logs.")
            if not args.yes:
                agent_id = input("Enter existing Dialogflow Agent ID (if any): ").strip()

        if agent_id:
            print(f"✅ Dialogflow Agent Ready: {agent_id}")

        # 3. LangSmith Setup
        print("\nSetting up LangSmith...")
        if args.langsmith_project:
            langchain_project = args.langsmith_project
        else:
            langchain_project = (
                input(f"Enter LangSmith Project Name (default: {project_id}): ").strip()
                or project_id
            )

        # 4. Update Config
        update_env_file(project_id, agent_id, langchain_project)

        print("\n✨ Setup Complete! ✨")
        print("Please verify the new settings in .env")
        print(
            f"Dialogflow Console: https://dialogflow.cloud.google.com/cx/projects/{project_id}/locations/global/agents/{agent_id}"
        )

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
