# graph_runner.py
from langgraph_setup import jailbreak_graph, JailbreakAttemptState
import datetime

def _create_result_dict(final_state: dict, task: dict, strategy: dict) -> dict:
    """Helper function to create a standardized result dictionary."""
    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "task_id": task.get("id"),
        "task_prompt": task.get("prompt"),
        "strategy_id": strategy.get("id"),
        "strategy_name": strategy.get("name"),
        "target_model_name": final_state.get("target_model_name"),
        "judge_model_name": final_state.get("judge_model_name"),
        "crafter_model_name": final_state.get("crafter_model_name"),
        "crafted_jailbreak_prompt": final_state.get("crafted_jailbreak_prompt"),
        "target_llm_response": final_state.get("target_llm_response"),
        "final_rating": final_state.get("final_rating"),
        "verdict_reasoning": final_state.get("verdict_reasoning"),
        "error_message": final_state.get("error_message"),
        "detailed_log": final_state.get("log")
    }

def run_single_jailbreak_attempt(
    task: dict, 
    strategy: dict, 
    target_model_name: str, 
    judge_model_name: str,
    crafter_model_name: str,
    ui_placeholders: dict = None
) -> dict:
    """
    Runs a single task-strategy pair through the jailbreak graph.
    This function NO LONGER writes to the log file. It only returns the result dictionary.
    The calling function is responsible for logging the result.
    """
    initial_state = JailbreakAttemptState(
        task=task,
        strategy=strategy,
        target_model_name=target_model_name,
        judge_model_name=judge_model_name,
        crafter_model_name=crafter_model_name,
        ui_placeholders=ui_placeholders or {},
        crafted_jailbreak_prompt=None,
        target_llm_response=None,
        final_rating=None,
        verdict_reasoning=None,
        error_message=None,
        log=[]
    )

    final_state = jailbreak_graph.invoke(initial_state)
    
    return _create_result_dict(final_state, task, strategy)