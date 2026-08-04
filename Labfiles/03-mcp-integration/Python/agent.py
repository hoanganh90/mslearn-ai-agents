import os
from dotenv import load_dotenv

# Add references
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool
from openai.types.responses.response_input_param import McpApprovalRequest, McpApprovalResponse, ResponseInputParam

# Load environment variables from .env file
load_dotenv()
project_endpoint = os.getenv("PROJECT_ENDPOINT")
model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
agent_name = "mcp-agent"
# Connect to the agents client
with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=project_endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):

    # Initialize agent MCP tool
    mcp_tool = MCPTool(
        server_label="MCPTool",
        server_url="https://learn.microsoft.com/api/mcp",
        require_approval="always",
    )
    
    # Create a new agent with the MCP tool
    agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
            instructions="You are a helpful agent that can use MCP tools to assist users. ",
            tools=[mcp_tool],
            model=model_deployment
        ),
    )
    print(f"Created agent version: {agent.version} {agent.name}")

    # Create conversation thread
    conversation = openai_client.conversations.create()
    print(f"Created conversation: {conversation.id}")


    # Send initial request that will trigger the MCP tool
    response = openai_client.responses.create(
        conversation=conversation.id,
        input="Give me the Azure CLI commands to create an Azure Container App with a managed identity and assign it the 'Storage Blob Data Contributor' role on a storage account.",
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}}
    )
    print(f"Created message: {response.id}")

    # Process any MCP approval requests that were generated
    approval_responses = []
    for item in response.output:
        print("OUTPUT ITEM:", item.type, getattr(item, "server_label", None), getattr(item, "id", None))
        if item.type == "mcp_approval_request" and item.id:
            approval_responses.append(McpApprovalResponse(
                type="mcp_approval_response",
                approved=True,
                approval_request_id=item.id,
                server_label=item.server_label
            ))
    print("Final input list:", approval_responses)
    if approval_responses:
        response = openai_client.responses.create(
            previous_response_id=response.id,
            input=approval_responses,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}}
        )
        print(f"Created follow-up message: {response.id}")
    else:
        print("No MCP approval request found; skipping follow-up.")
    # Clean up resources by deleting the agent version
    project_client.agents.delete_version(agent.name, agent.version)
    print("Agent deleted successfully.")
