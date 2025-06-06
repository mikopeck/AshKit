# graph_runner.py
from langgraph_setup import jailbreak_graph, JailbreakAttemptState
import json
import os
import datetime

RESULTS_LOG_FILE = os.path.join("results", "jailbreak_log.jsonl")
os.makedirs("results", exist_ok=True)

def log_and_return_result(final_state: dict, task: dict, strategy: dict) -> dict:
    """Helper function to create a log entry and a result dictionary."""
    log_entry = {
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
    
    with open(RESULTS_LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    return log_entry

def run_single_jailbreak_attempt(
    task: dict, 
    strategy: dict, 
    target_model_name: str, 
    judge_model_name: str,
    crafter_model_name: str,
    ui_placeholders: dict = None
) -> dict:
    """
    Runs a single task-strategy pair through the jailbreak graph for the UI.
    Returns a dictionary suitable for direct use in Streamlit session state.
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
    return log_and_return_result(final_state, task, strategy)

def run_single_jailbreak_attempt_for_comprehensive(
    task: dict, 
    strategy: dict, 
    target_model_name: str, 
    judge_model_name: str,
    crafter_model_name: str,
    ui_placeholders: dict = None
) -> dict:
    """
    A separate runner for the comprehensive mode. It does NOT write to the final
    log file itself, as that is handled by the comprehensive runner's state.
    It returns the full result dictionary.
    """
    # This function is almost identical to the main one but crucially
    # does not write to the log file, allowing the comprehensive runner to
    # collect results before deciding what to do with them.
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
    
    # Just construct the dictionary, don't write it to the file
    result_dict = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "task_id": task.get("id"),
        "task_prompt": task.get("prompt"),
        "strategy_id": strategy.get("id"),
        "strategy_name": strategy.get("name"),
        "target_model_name": target_model_name,
        "judge_model_name": judge_model_name,
        "crafter_model_name": crafter_model_name,
        "crafted_jailbreak_prompt": final_state.get("crafted_jailbreak_prompt"),
        "target_llm_response": final_state.get("target_llm_response"),
        "final_rating": final_state.get("final_rating"),
        "verdict_reasoning": final_state.get("verdict_reasoning"),
        "error_message": final_state.get("error_message"),
    }
    return result_dict