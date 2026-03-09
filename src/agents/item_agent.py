from strands import Agent, tool
from strands.models import BedrockModel
from src.tools.item_tools import get_look_images, get_look_composition
from strands_tools import retrieve

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",
)

ITEM_PROMPT = """
Role:
Handle questions about individual items, looks, and metadata.
To find specific details (e.g. reference codes, materials, or design features) for a specific named item, use the retrieve tool. Pass the item name into the query, instead of the full query. Do not pass look numbers.
To get the composition of a look, use the get_look_composition tool. Only use it when you have a look number. 
To retrieve the runway images of a certain look, use the get_look_images tool. Only use it when you have a look number.

Guidelines:
Never ask the user for look numbers.
When tools require look numbers, do not use them when you don't have one.
If retrieved results yield a low score, retry with a lower threshold. If results remain below the threshold, return them anyway but state that they are provided with lower confidence.
"""

@tool
def item_assistant(query: str) -> str:
    """
    Handle queries about single items, looks, and their metadata.
    
    Args:
    query (str): A question about an item.

    Returns: 
    Textual response with item information.
    """
    try:
        item_agent = Agent(
            model=bedrock_model,
            system_prompt=ITEM_PROMPT,
            tools=[get_look_images, get_look_composition, retrieve]
        )

        response = item_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in item assistant: {str(e)}"