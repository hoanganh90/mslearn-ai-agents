import os
import asyncio
import json
from dotenv import load_dotenv
from contextlib import AsyncExitStack
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam

# Add references


# Clear the console
os.system('cls' if os.name=='nt' else 'clear')

# Load environment variables from .env file
load_dotenv()
project_endpoint = os.getenv("PROJECT_ENDPOINT")
model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")

async def connect_to_server(exit_stack: AsyncExitStack):
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )

    # Start the MCP server
    studio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
    stdio, write = studio_transport

    # Create an MCP client session
    session = await exit_stack.enter_async_context(ClientSession(stdio, write))
    await session.initialize()  

    # List available tools
    response = await session.list_tools()
    tools = response.tools
    print("\nAvailable MCP tools: ", [tool.name for tool in tools])
   

    return session

async def chat_loop(session):

    # Connect to the agents client
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=project_endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):

        # Get the mcp tools available from the server
        response = await session.list_tools()
        tools = response.tools

        # Build a function for each tool
        def make_tool_func(tool_name):
            async def tool_func(*args, **kwargs):
                # Call the MCP tool
                result = await session.call_tool(tool_name, *args, **kwargs)
                return result
            tool_func.__name__ = tool_name
            return tool_func

        # Store the functions in a dictionary
        functions_dict = {tool.name: make_tool_func(tool.name) for tool in tools}

        # Create FunctionTool definitions for the agent
        mcp_function_tools: FunctionTool = []
        for tool in tools:
            function_tool = FunctionTool(
                name=tool.name,
                description=tool.description,
                parameters= {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                },
                strict=True
            )
            mcp_function_tools.append(function_tool)

        # Create the agent
        agent = project_client.agents.create_version(
            agent_name="inventory-agent",
            definition=PromptAgentDefinition(
                instructions="You are a helpful agent that can use MCP tools to assist users. ",
                tools=mcp_function_tools,
                model=model_deployment
            ),
        )

        # Create a thread for the chat session
        conversation = openai_client.conversations.create()

        # Create an input list to hold function call outputs to send back to the model
        input_list: ResponseInputParam = []

        while True:
            user_input = input("Enter a prompt for the inventory agent. Use 'quit' to exit.\nUSER: ").strip()
            if user_input.lower() == "quit":
                print("Exiting chat.")
                break

            # Send a prompt to the agent
            openai_client.conversations.items.create(
                conversation_id=conversation.id,
                items=[{"type": "message", "role": "user", "content": user_input}],
            )

            # Retrieve the agent's response, which may include function calls to the MCP server tools
            response = openai_client.responses.create(
                conversation=conversation.id,
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input=input_list,
            )

            # Check the run status for failures
            if response.status == "failed":
                print(f"Response failed: {response.error}")

            # Process function calls
            for item in response.output:
                if item.type == "function_call":
                    function_name = item.function_call.name
                    function_args = json.loads(item.function_call.arguments)
                    print(f"Agent requested function call: {function_name} with arguments: {function_args}")

                    # Call the corresponding MCP tool function
                    if function_name in functions_dict:
                        tool_func = functions_dict[function_name]
                        tool_result = await tool_func(**function_args)
                        print(f"Function call result: {tool_result}")

                        # Prepare the function call output to send back to the model
                        function_output = FunctionCallOutput(
                            type="function_call_output",
                            name=function_name,
                            output=tool_result,
                            id=item.id
                        )
                        input_list.append(function_output)
                    else:
                        print(f"Function {function_name} not found among available tools.")

            # Send function call outputs back to the model and retrieve a response
            response = openai_client.responses.create(
                conversation=conversation.id,
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input=input_list,
            )
           
        # Delete the agent when done
        print("Cleaning up agents:")
        project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
        print("Deleted inventory agent.")


async def main():
    import sys
    exit_stack = AsyncExitStack()
    try:
        session = await connect_to_server(exit_stack)
        await chat_loop(session)
    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())
