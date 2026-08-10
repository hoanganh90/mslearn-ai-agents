import asyncio
import os
from urllib import response
from anyio import Path
from dotenv import load_dotenv

# Add references
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.projects import AzureOpenAIClient


load_dotenv()
def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        # Load Configuration from environment variables
        load_dotenv()
        foundry_endpoint = os.getenv("PROJECT_ENDPOINT")
        agent_name = os.getenv("AZURE_AGENT_NAME")
        model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
        speech_file_path = Path(__file__).parent / "output.wav"
        # Create a credential with a token provider
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), scopes=["https://cognitiveservices.azure.com/.default"]
        )
        # Get project client
        project_client = AzureOpenAIClient(
            endpoint=foundry_endpoint,
            credential=DefaultAzureCredential(), 
            api_version="2024-06-01-preview")                              
        # Get an OpenAI client
        with project_client.audio.speech.with_streaming_response.create(
            model=model_deployment,
            input=[{"role": "user", "content": "Hello, how are you?"}]
            instructions="Speak in a serious tone",
        ) as response:
        response.stream_to_file(speech_file_path)

        # Use the agent to get a response
       

    except Exception as e:
        print(f"Error: {e}")
if __name__ == "__main__":
    main()