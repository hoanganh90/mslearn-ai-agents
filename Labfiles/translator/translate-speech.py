from dotenv import load_dotenv
import os
from playsound3 import playsound
import winsound
# Import namespaces from the Azure AI Projects SDK
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
from azure.ai.projects import AIProjectClient

def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')

        # Load Configuration from environment variables
        load_dotenv()
        foundry_endpoint = os.getenv("FOUNDARY_ENDPOINT")
        agent_name = os.getenv("AGENT_NAME")
        text_translation_endpoint = os.getenv("MODEL_ENDPOINT")
        text_translation_key = os.getenv("MODEL_KEY")
        region = os.getenv("MODEL_REGION", "swedencentral")

        # Get project client
        text_translation_credential = AzureKeyCredential(text_translation_key) if text_translation_key else DefaultAzureCredential()
        text_translation_client = TextTranslationClient(
            endpoint=text_translation_endpoint, 
            credential=text_translation_credential,     
            region=region
        )

        # Choose target language
        languageResponse = text_translation_client.get_supported_languages(scope="translation")
        supported_languages = languageResponse.translation
        
        # Print list of supported languages
        print("Supported languages:")
        for code, lang in supported_languages.items():
            print(f"  {lang.name} ({code})")
        print("Enter target language code (e.g., es, fr, de, it, ja): ")
        target_language = input()
        if target_language not in supported_languages:
            print("Invalid language code. Please try again.")
            return

        # Get project client
        project_client = AIProjectClient(credential=DefaultAzureCredential(), 
                                          endpoint=foundry_endpoint)
        
        #Get an OpenAI client
        openai_client = project_client.get_openai_client()
        
        # Loop until user quits
        while True:
            # Get user input
            prompt = input("Enter your message (or quit): ")
            if prompt.lower() == "quit" or len(prompt) == 0:
                break
            else:
                # Use the agent to get response
                response = openai_client.response.create(
                    model=agent_name,
                    input=[{"role": "user", "content": prompt}],
                    extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}}
                )
                print(f"{agent_name}: {response.output[0].message.content}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()