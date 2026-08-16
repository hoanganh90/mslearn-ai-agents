import os
from urllib.request import urlopen, Request
import base64
from pathlib import Path
from dotenv import load_dotenv

# Add references
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

def main():
    # Clear the console
    os.system('cls' if os.name=='nt' else 'clear')
    try:
        # Get configuration settings
        load_dotenv()
        openai_endpoint = os.getenv("OPENAI_ENDPOINT")
        model_deployment = os.getenv("MODEL_NAME")

        # Create an OpenAI client
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default" 
        )
        client = OpenAI(
            base_url=openai_endpoint,
            api_key=token_provider
        )
        # Initialize prompts
        system_message = "You are an AI assustant in a grocery store that sells fruit. You provide detailed answers to questions about produce."
        prompt = ""
        while True:
            prompt = input("\n Ask a question about the image \n (or type quit to exit)\n")
            if prompt.lower() == "quit":
                break
            elif len(prompt) == 0:
                print("Please enter a question\n")
            else:
                print("Gretting a response ...\n")

                # Get a response to image input
                image_url = "Labfiles\vision-agent\mango-fruit-veggipedia.png"
                response = client.responses.create(
                    model=model_deployment,
                    input= [
                        {"role": "developer", "content": system_message},
                        {
                            "role": "user", "content":[
                                {"type": "input_text", "text": prompt},
                                {"type": "input_image", "image_url": image_url}
                            ]
                        }
                    ]
                )
                print(response.output_text)
    except Exception as ex:
        print(ex)

if __name__ == "__main__":
    main()