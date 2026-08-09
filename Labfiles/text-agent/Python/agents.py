import asyncio
import os
from dotenv import load_dotenv

# Add references
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectsClient


load_dotenv()

def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        # Load Configuration from environment variables
        load_dotenv()
        foundry_endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT")
        agent_name = os.getenv("AZURE_AGENT_NAME")

        # Get project client
        project_client = AIProjectsClient(credential=DefaultAzureCredential(), 
                                          endpoint=foundry_endpoint)
        # Get an OpenAI client
        openai_client = project_client.get_openai_client()

        # Use the agent to get a response
        prompt = input("Enter your prompt: ")
        response = openai_client.get_response(
            input=[{"role": "user", "content": prompt}],
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}}
        )
        print(f"{agent_name} Response: {response.output_text}")

    except Exception as e:
        print(f"Error: {e}")
if __name__ == "__main__":
    asyncio.run(main())