from strands_evals import Case, Experiment, ActorSimulator
from strands_evals.evaluators import HelpfulnessEvaluator, GoalSuccessRateEvaluator, FaithfulnessEvaluator, ToolSelectionAccuracyEvaluator, OutputEvaluator, TrajectoryEvaluator
from strands_evals.mappers import StrandsInMemorySessionMapper
from strands_evals.telemetry import StrandsEvalsTelemetry
import sys
import os
import asyncio
import json
import boto3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def load_secrets():
    secret_name = "dh-agent/config"
    region_name = "us-east-1"

    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secrets = json.loads(response['SecretString'])

    for key, value in secrets.items():
        os.environ[key] = str(value)

load_secrets()

from src.orchestration.orchestrator import Orchestrator

telemetry = StrandsEvalsTelemetry().setup_in_memory_exporter()
memory_exporter = telemetry.in_memory_exporter

def get_multiturn_response(case: Case) -> str:
    simulator = ActorSimulator.from_case_for_user_simulator(
        case=case,
        model='us.amazon.nova-pro-v1:0',
        max_turns=5
    )
    simulator.agent.model = 'us.amazon.nova-pro-v1:0'
    simulator.model_id = 'us.amazon.nova-pro-v1:0'
    
    agent = Orchestrator()
    agent.agent.trace_attributes = {
        "gen_ai.conversation.id": case.session_id,
        "session.id": case.session_id
    }
    
    conversation_history = []
    all_spans = []
    user_message = case.input
    while simulator.has_next():
        memory_exporter.clear()

        agent_response = agent.ask(user_message)
        agent_message = str(agent_response)
        
        turn_spans = list(memory_exporter.get_finished_spans())
        all_spans.extend(turn_spans)

        conversation_history.append({
            "role": "agent",
            "message": agent_message
        })

        user_result = simulator.act(agent_message)
        user_message = str(user_result.structured_output.message)

        conversation_history.append({
            "role": "user",
            "message": user_message,
            "reasoning": user_result.structured_output.reasoning
        })

    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(all_spans, session_id=case.session_id)

    return {"output": agent_message, "trajectory": session, "conversation_history": conversation_history}


async def get_response(case: Case) -> str:
    agent = Orchestrator()
    agent.agent.trace_attributes = {
        "gen_ai.conversation.id": case.session_id,
        "session.id": case.session_id
    }
    response = agent.ask(case.input)

    finished_spans = memory_exporter.get_finished_spans()
    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(finished_spans, session_id=case.session_id)

    return {"output": str(response), "trajectory": session}

OUTPUT_RUBRIC = """
Evaluate the response based on:
1. Accuracy - Is the information correct?
2. Completeness - Does it fully answer the question?
3. Clarity - Is it easy to understand?

Score 1.0 if all criteria are met excellently.
Score 0.5 if some criteria are partially met.
Score 0.0 if the response is inadequate.
"""

TRAJECTORY_RUBRIC = """
The trajectory should be in the correct order with all of the steps as the expected.
The agent should know when and what action is logical. Strictly score 0 if any step is missing.
"""

evaluators = [
    OutputEvaluator(rubric=OUTPUT_RUBRIC, model='us.amazon.nova-pro-v1:0'),
    TrajectoryEvaluator(rubric=TRAJECTORY_RUBRIC, model='us.amazon.nova-pro-v1:0'),
    HelpfulnessEvaluator(model='us.amazon.nova-pro-v1:0'),
    FaithfulnessEvaluator(model='us.amazon.nova-pro-v1:0'),
    ToolSelectionAccuracyEvaluator(model='us.amazon.nova-pro-v1:0'),
    GoalSuccessRateEvaluator(model='us.amazon.nova-pro-v1:0')
]

def create_dataset(mode="followups2"):
    input_data = f"datasets/eval_{mode}.json"
    with open(input_data, 'r') as f:
        eval_data = json.load(f)

    test_cases = []

    for conversation in eval_data:
        test_cases.append(Case[str, str](
            input=conversation["query"],
            expected_output=conversation["reference"],
            metadata=conversation["metadata"],
            expected_trajectory=conversation["expected_trajectory"]
        ))
    
    return test_cases

test_cases = create_dataset()

experiment = Experiment(cases=test_cases, evaluators=evaluators)
reports = experiment.run_evaluations(get_multiturn_response)

# Display results
for report in reports:
    print(f"\n{'='*60}")
    print(f"Evaluator: {report.evaluator_name}")
    print(f"{'='*60}")
    report.run_display()

# async def run_async_evaluation():
#     experiment = Experiment[str, str](cases=test_cases, evaluators=evaluators)
#     reports = await experiment.run_evaluations_async(get_multiturn_response)

#     for report in reports:
#         report.run_display()

#     return reports

# if __name__ == "__main__":
#     report = asyncio.run(run_async_evaluation())