from strands import Agent, tool, AgentSkills
from strands.models import BedrockModel
from src.tools.search_tools import listing_search, general_search
from src.agents.handlers import AgentSteeringHandler

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",
)

plugin = AgentSkills(skills="src/agents/skills/search_skills")

SEARCH_PROMPT = """
Role:
Provide verified market and historical context via web searches.
"""

handler = AgentSteeringHandler(
    system_prompt="""
    You are providing guidance to ensure proper formatting of information.

    Guidance:
    For historical data, cite the source URL for every fact. For marketplace results, provide only the direct listing URL once per item.
    
    When the tools return their responses, evaluate the text and deliver the final response directly to the user.
    """
)

@tool
def search_assistant(query: str) -> str:
    """
    Handle queries requiring web search.

    Args:
    query (str): A question requiring external web search.

    Returns:
    Textual response synthesizing information from web sources, including cited URLs where applicable.
    """
    try:
        archive_agent = Agent(
            model=bedrock_model,
            system_prompt=SEARCH_PROMPT,
            tools=[general_search, listing_search],
            plugins=[plugin, handler]
        )

        response = archive_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in search assistant: {str(e)}"