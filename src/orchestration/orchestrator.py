from strands import Agent
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager
from strands.agent.conversation_manager import SlidingWindowConversationManager, SummarizingConversationManager
from src.agents.archive_agent import archive_assistant
from src.agents.search_agent import search_assistant
from src.agents.conversation_managers import ProactiveSummarizingConversationManager
from src.agents.hooks import NotifyOnlyGuardrailsHook, LimitToolCounts
from src.agents.handlers import AgentSteeringHandler

ORCHESTRATOR_PROMPT = """
Role: 
You are the lead archival coordinator for the Dior Homme Autumn/Winter 2004 "Victim of the Crime" collection. Your goal is to answer user queries accurately by delegating work to specialized subagents and synthesizing their responses into a single, coherent response.

Analyze the user query and determine which subagent(s) to invoke:
1. For queries regarding specific items, looks, or the full collection, use the archive_assistant tool. 
2. For queries requiring web search (such as for listings, or for information not documented in the knowledge base such as music or theming), use the search_assistant tool. 
"""

handler = AgentSteeringHandler(
    system_prompt="""
    You are providing guidance to ensure proper formatting of information.

    Guidance:
    Maintain a neutral tone.
    Do not include internal monologues, reasoning steps, or tags like <thinking>. Avoid mentioning subagents or tools.
    
    When subagents return their analysis, evaluate the combined text and deliver the final response directly to the user.
    """
)

class Orchestrator:
    """Wrapper class for the multi-agent orchestration system."""

    def __init__(self):
        self.model = BedrockModel(model_id="us.amazon.nova-2-lite-v1:0",
                                  temperature=0.0,
                                  max_tokens=12000)
                                #   guardrail_id="ys4jzzz12h6r",
                                #   guardrail_version="14",
                                #   guardrail_trace="enabled")
        #self.session_manager = FileSessionManager(session_id='new-session')
        self.conversation_manager = ProactiveSummarizingConversationManager() #SlidingWindowConversationManager(window_size=20, should_truncate_results=True, per_turn=5)
        self.agent = Agent(
            model=self.model,
            system_prompt=ORCHESTRATOR_PROMPT,
            #session_manager=self.session_manager,
            conversation_manager=self.conversation_manager,
            callback_handler=None,
            tools=[archive_assistant, search_assistant],
            hooks=[NotifyOnlyGuardrailsHook("ys4jzzz12h6r", "14"), LimitToolCounts(max_tool_counts={"archive_assistant": 3, "search_assistant": 3})],
            plugins=[handler]
        )

    def ask(self, query: str):
        try:
            response = self.agent(query)
            print(f"\n{'='*60}")
            print(f"Response Summary")
            print(f"{'='*60}")
            print(response.metrics.get_summary())
            if response.stop_reason == "guardrail_intervened":
                return "Sorry, this question is out of scope. This archive is strictly dedicated to Dior Homme Autumn/Winter 2004."
            return response.message
        except Exception as e:
            return f"Error in orchestrator: {str(e)}"