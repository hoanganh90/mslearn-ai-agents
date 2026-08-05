import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables
load_dotenv()
project_endpoint = os.getenv("PROJECT_ENDPOINT")
agent_name = os.getenv("AGENT_NAME")

# Validate configuration
if not project_endpoint or not agent_name:
    raise ValueError("PROJECT_ENDPOINT and AGENT_NAME must be set in .env file")

print(f"Connecting to project: {project_endpoint}")
print(f"Using agent: {agent_name}\n")

# TODO: Connect to the project and create a conversation
# Add your code here to:
# 1. Create DefaultAzureCredential
credential = DefaultAzureCredential(
    exclude_environment_credential=False,
    exclude_managed_identity_credential=True,
)
# 2. Create AIProjectClient with endpoint
project_client = AIProjectClient(
    endpoint=project_endpoint, 
    credential=credential)
# 3. Get the OpenAI client
openai_client = project_client.get_openai_client()
# 4. Get the agent by name
agent = project_client.agents.get(agent_name=agent_name)
print(f"Connected to agent: {agent.name} (version: {agent.versions})\n")
# 5. Create a new conversation
conversation = openai_client.conversations.create(items=[])
print(f"Created conversation: {conversation.id}\n")


# Conversation history for context (client-side tracking)
conversation_history = []


def send_message_to_agent(user_message):
    """
    Send a message to the agent and handle the response using the conversations API.
    """
    try:
        print("\nAgent: ", end="", flush=True)
        
        # TODO: Add user message to conversation and get response
        # Add your code here to:
        # 1. Add the user message to the conversation using conversations.items.create()
        openai_client.conversations.items.create(
            conversation.id,
            items=[{
                "type": "message",
                "role": "user",
                "content": user_message
            }]
        )

        # store in conversation history (client-side)
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        # 2. Create a response using responses.create() with agent reference
        response = openai_client.responses.create(
            conversation=conversation.id,
            input=user_message,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}}
        )
        # Check if the response output contains an MCP approval request and handle it
        approval_requests = None
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'type') and item.type == "mcp_approval_request":
                    approval_requests = item
                    break
        # Handle approval requests if present
        if approval_requests:
            print(f"\nAgent requested approval for MCP tool call: {approval_requests.id}")
            print(f"Server label: {approval_requests.server_label}")
            # Parse and display the arguments for the MCP tool call
            import json
            try:
                args = json.loads(approval_requests.arguments)
                print(f"Arguments: {json.dumps(args, indent=2)}")
            except json.JSONDecodeError:
                print("Failed to parse MCP tool call arguments.")
            approval_input = input("Approve this MCP tool call? (y/n): ").strip().lower()
            if approval_input == 'y':
                print("Approving MCP tool call...")
                #Create approval response
                approval_response = {
                    
                    "type": "mcp_approval_response",
                    "approve": True,
                    "approval_request_id": approval_requests.id
                }
            else:
                print("Declining MCP tool call...")
                #Create denial response
                approval_response = {
                    "type": "mcp_approval_response",
                    "approve": False,
                    "approval_request_id": approval_requests.id
                }

            # Add the approval response to the conversation and get the next response
            openai_client.conversations.items.create(
                conversation.id,
                items=[approval_response]
            )
            # Get the next response after approval/denial
            response = openai_client.responses.create(
                conversation=conversation.id,
                input=approval_response,
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}}
            )
        # 3. Extract and display the response text 
        # Extract the response text
        if response and response.output_text:
            response_text = response.output_text
            
            print(f"{response_text}\n")
            
            # Check for citations if available
            if hasattr(response, 'citations') and response.citations:
                print("\nSources:")
                for citation in response.citations:
                    print(f"  - {citation.content if hasattr(citation, 'content') else 'Knowledge Base'}")
            
            # Store in conversation history (client-side)
            conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            return response_text
        else:
            print("No response received.\n")
            return None
    except Exception as e:
        print(f"\n\nError: {str(e)}\n")
        return None


def display_conversation_history():
    """
    Display the full conversation history.
    """
    print("\n" + "="*60)
    print("CONVERSATION HISTORY")
    print("="*60 + "\n")
    
    for turn in conversation_history:
        role = turn["role"].upper()
        content = turn["content"]
        print(f"{role}: {content}\n")
    
    print("="*60 + "\n")


def main():
    """
    Main interaction loop.
    """
    print("Contoso Product Expert Agent")
    print("Ask questions about our outdoor and camping products.")
    print("Type 'history' to see conversation history, or 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == 'quit':
                print("\nEnding conversation...")
                break
                
            if user_input.lower() == 'history':
                display_conversation_history()
                continue
            
            # Send message and get response
            send_message_to_agent(user_input)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}\n")
    
    print("\nConversation ended.")


if __name__ == "__main__":
    main()
