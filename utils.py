# utils.py
import json
import os

TASKS_FILE = os.path.join("data", "tasks.json")
STRATEGIES_FILE = os.path.join("data", "strategies.json")

def load_json_data(filepath: str, default_data=None):
    if default_data is None:
        default_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {filepath}. Returning default.")
            return default_data
    return default_data

def save_json_data(filepath: str, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_tasks():
    return load_json_data(TASKS_FILE, [
        {"id": "default_task", "description": "Default task", "prompt": "Explain quantum physics.", "harm_category": "benign"}
    ])

def add_task(new_task: dict):
    """Adds a new task to the tasks.json file."""
    tasks = load_tasks()
    if any(t['id'] == new_task['id'] for t in tasks):
        raise ValueError(f"Task with ID {new_task['id']} already exists.")
    tasks.append(new_task)
    save_json_data(TASKS_FILE, tasks)

def load_strategies():
    return load_json_data(STRATEGIES_FILE, [
        {"id": "default_strategy", "name": "Default Strategy", "template": "Please answer this: {task_prompt}"}
    ])

def add_strategy(new_strategy: dict):
    strategies = load_strategies()
    if any(s['id'] == new_strategy['id'] for s in strategies):
        raise ValueError(f"Strategy with ID {new_strategy['id']} already exists.")
    strategies.append(new_strategy)
    save_json_data(STRATEGIES_FILE, strategies)

def load_results_log(log_file_path):
    results = []
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding='utf-8') as f:
            for line in f:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Skipping malformed line in log: {line.strip()}")
    return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)