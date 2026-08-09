import asyncio
import os
from dotenv import load_dotenv

# Add references
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


load_dotenv()

def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        # Load Configuration from environment variables
        load_dotenv()
        foundry_endpoint = os.getenv("PROJECT_ENDPOINT")
        agent_name = os.getenv("AZURE_AGENT_NAME")
        # model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
        # Get project client
        project_client = AIProjectClient(credential=DefaultAzureCredential(), 
                                          endpoint=foundry_endpoint)
        # Get an OpenAI client
        openai_client = project_client.get_openai_client()

        # Use the agent to get a response
        prompt = input("Enter your prompt: ")
        response = openai_client.responses.create(
            input=[{"role": "user", "content": prompt}],
            extra_body={"agent_reference": {
                "name": agent_name, 
                "type": "agent_reference", 
                # "deployment": model_deployment
                }
            }
        )
        print(f"{agent_name} Response: {response.output_text}")

    except Exception as e:
        print(f"Error: {e}")
if __name__ == "__main__":
    main()