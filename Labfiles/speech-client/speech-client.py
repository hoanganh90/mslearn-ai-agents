from dotenv import load_dotenv
import os
from playsound3 import playsound
import winsound
# Import namespaces from the Azure AI Projects SDK
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')

        # Load Configuration from environment variables
        load_dotenv()
        foundry_endpoint = os.getenv("FOUNDARY_ENDPOINT")
        agent_name = os.getenv("AGENT_NAME")

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