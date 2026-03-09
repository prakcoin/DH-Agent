from strands import Agent, tool
from strands.models import BedrockModel
from src.tools.aggregation_tools import get_collection_items, get_collection_summary, get_item_counts
from strands_tools import retrieve

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",
)


AGGREGATION_PROMPT = """
Role:
Answer questions that require aggregation or analysis across the entire collection.
To perform multi-item search, use the retrieve tool. Pass the relevant terms (item name, metadata), not the full query.
To get a full collection summary, use the get_collection_summary tool. Do not pass any parameters.
To get specific counts, use the get_item_counts tool. Pass the relevant terms (item name, metadata), not the full query.

Guidelines:
Exclude generic functional components (buttons, belts, solids) unless explicitly asked.
Consolidate duplicate entries.
If retrieved results yield a low score, retry with a lower threshold. If results remain below the threshold, return them anyway but state that they are provided with lower confidence.
"""

@tool
def aggregation_assistant(query: str) -> str:
    """
    Handle collection-wide queries about multiple items, looks, and their metadata.

    Args:
    query (str): A question about aggregation.

    Returns: 
    Textual response with aggregated information.
    """
    try:
        aggregation_agent = Agent(
            model=bedrock_model,
            system_prompt=AGGREGATION_PROMPT,
            tools=[get_collection_summary, get_item_counts, retrieve]
        )

        response = aggregation_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in aggregation assistant: {str(e)}"