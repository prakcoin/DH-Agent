from typing import TYPE_CHECKING, Any, Literal, cast
from pydantic import BaseModel, Field
from strands import Agent
from strands.vended_plugins.steering.core.handler import SteeringHandler
from strands.vended_plugins.steering import Guide, ModelSteeringAction, Proceed, SteeringHandler
from strands.models import BedrockModel
from strands.types.content import Message

if TYPE_CHECKING:
    from strands import Agent as AgentType

class ToneDecision(BaseModel):
    """Structured output for output evaluation."""

    decision: Literal["proceed", "guide"] = Field(
        description="Steering decision: 'proceed' to accept, 'guide' to provide feedback"
    )
    reason: str = Field(description="Clear explanation of the decision and any guidance provided")


class ModelOutputSteeringHandler(SteeringHandler):
    """Steering handler that validates model responses meet guidelines."""

    name = "model_output_steering"

    def __init__(self, system_prompt) -> None:
        """Initialize the model output steering handler."""
        super().__init__()

        self._system_prompt = system_prompt

        self._model = BedrockModel(
            model_id="us.amazon.nova-pro-v1:0",
        )

    async def steer_after_model(
        self,
        *,
        agent: "AgentType",
        message: Message,
        stop_reason: Literal[
            "content_filtered",
            "end_turn",
            "guardrail_intervened",
            "interrupt",
            "max_tokens",
            "stop_sequence",
            "tool_use",
        ],
        **kwargs: Any,
    ) -> ModelSteeringAction:
        """Validate that model responses meet guidelines."""
        if stop_reason != "end_turn":
            return Proceed(reason="Not a final response")

        content = message.get("content", [])
        text = " ".join(block.get("text", "") for block in content if block.get("text"))
        if not text:
            return Proceed(reason="No text content to evaluate")

        steering_agent = Agent(system_prompt=self._system_prompt, model=self._model, callback_handler=None)
        result = steering_agent(f"Evaluate this message:\n\n{text}", structured_output_model=ToneDecision)
        decision: ToneDecision = cast(ToneDecision, result.structured_output)

        match decision.decision:
            case "proceed":
                return Proceed(reason=decision.reason)
            case "guide":
                guidance = f"""Your previous response was NOT shown to the user.
{decision.reason}
Please provide a new response."""
                return Guide(reason=guidance)
            case _:
                return Proceed(reason="Unknown decision, defaulting to proceed")