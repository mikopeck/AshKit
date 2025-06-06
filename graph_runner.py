# graph_runner.py
from langgraph_setup import jailbreak_graph, JailbreakAttemptState
import json
import os
from datetime import datetime

RESULTS_LOG_FILE = os.path.join("results", "jailbreak_log.jsonl")
os.makedirs("results", exist_ok=True)

def run_single_jailbreak_attempt(
    task: dict, 
    strategy: dict, 
    target_model_name: str, 
    judge_model_name: str,
    crafter_model_name: str, # New parameter
    ui_placeholders: dict = None # New parameter for UI elements
) -> dict:
    """
    Runs a single task-strategy pair through the jailbreak graph.
    """
    initial_state = JailbreakAttemptState(
        task=task,
        strategy=strategy,
        target_model_name=target_model_name,
        judge_model_name=judge_model_name,
        crafter_model_name=crafter_model_name, # Pass it in
        ui_placeholders=ui_placeholders or {}, # Pass it in
        crafted_jailbreak_prompt=None,
        target_llm_response=None,
        final_rating=None, # Note: key is 'final_rating'
        verdict_reasoning=None,
        error_message=None,
        log=[]
    )

    final_state = jailbreak_graph.invoke(initial_state)
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": task.get("id"),
        "task_prompt": task.get("prompt"),
        "strategy_id": strategy.get("id"),
        "strategy_name": strategy.get("name"),
        "target_model_name": target_model_name,
        "judge_model_name": judge_model_name,
        "crafter_model_name": crafter_model_name,
        "crafted_jailbreak_prompt": final_state.get("crafted_jailbreak_prompt"),
        "target_llm_response": final_state.get("target_llm_response"),
        "final_rating": final_state.get("final_rating"), # --- FIX: Use 'final_rating' to match the state ---
        "verdict_reasoning": final_state.get("verdict_reasoning"),
        "error_message": final_state.get("error_message"),
        "detailed_log": final_state.get("log")
    }
    
    with open(RESULTS_LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    # Return a serializable dictionary, which is what 'log_entry' is
    result_for_df = log_entry.copy()
    # The detailed log can be large; maybe exclude it from the immediate in-memory representation
    result_for_df.pop("detailed_log", None)
    result_for_df.pop("crafted_jailbreak_prompt", None)
    result_for_df.pop("target_llm_response", None)
    return result_for_df