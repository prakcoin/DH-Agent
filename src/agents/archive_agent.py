from strands import Agent, tool, AgentSkills
from strands.models import BedrockModel
from src.tools.archive_tools.collection_inventory import get_collection_inventory
from src.tools.archive_tools.image_input import get_image_input
from src.tools.archive_tools.look_analysis import get_look_analysis
from strands_tools import retrieve
from src.agents.hooks import LimitToolCounts
from src.agents.handlers import AgentSteeringHandler

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
)

plugin = AgentSkills(skills="src/agents/skills/archive_skills")

PROMPT = """
Role:
Provide precise data on individual items, specific looks, and collection-wide analysis by utilizing the archival toolset.
Do not hallucinate item information. All information must be derived from the archive.
"""

handler = AgentSteeringHandler(
    system_prompt="""
    You are providing guidance to ensure proper formatting of information.

    Guidance:
    Consolidate duplicate entries.
    Do not provide tangential context, historical background, or related media unless specifically requested.

    When the tools return their responses, evaluate the text and deliver the final response directly to the user.
    """
)

@tool
def archive_assistant(query: str) -> str:
    """
    Handle all knowledge base queries related to the Dior Homme AW04 "Victim of the Crime" collection.
    
    Args:
    query (str): A question about an item.

    Returns: 
    Textual response synthesized from internal archival tools.
    """
    try:
        archive_agent = Agent(
            model=bedrock_model,
            system_prompt=PROMPT,
            tools=[get_collection_inventory, get_look_analysis, get_image_input, retrieve],
            plugins=[plugin, handler],
            hooks=[LimitToolCounts(max_tool_counts={"retrieve": 3})]
        )

        response = archive_agent(query)
        print(f"ALL ARCHIVE AGENT TOOLS {archive_agent.tool_registry.get_all_tools_config()} FELLA----------------------------")
        return str(response)
    except Exception as e:
        return f"Error in item assistant: {str(e)}"