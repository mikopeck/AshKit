# AshKit: LLM Red Teaming Toolkit

**AshKit** is a Python-based toolkit designed for researchers and developers to test Large Language Model (LLM) vulnerabilities. It offers two primary modes: **Model Profiling** to generate broad vulnerability reports and **Evolutionary Simulation** to breed and find the most effective jailbreak for a specific goal. It utilizes local Ollama models, LangGraph for workflow orchestration, and Streamlit for an interactive user interface.

**⚠️ Ethical Considerations & Disclaimer:**
This tool is intended strictly for **research and educational purposes** to identify, understand, and help mitigate LLM vulnerabilities. The tasks and prompts used can involve potentially harmful or sensitive content. Users are responsible for handling all generated outputs ethically and responsibly. Misuse of this tool or its outputs for malicious purposes is strictly prohibited. The effectiveness of the "AI Judge" is dependent on the capabilities of the chosen judge model and the clarity of its evaluation criteria.

---
## Features

* **Local LLM Interaction:** Leverages [Ollama](https://ollama.com/) to run LLMs locally for the target model being tested, the crafter model generating prompts, and the AI judge evaluating responses.
* **Two Testing Modes:**
    * **Model Profiling:** Automatically runs all tasks against all strategies to generate a comprehensive vulnerability profile of an LLM, complete with live visualizations showing its weaknesses as they are discovered.
    * **Evolutionary Simulation:** Concentrates on a single user-defined task, using a genetic algorithm to evolve and combine strategies over multiple generations to discover the most potent jailbreak prompts.
* **AI-Powered Evaluation:** An "AI Judge" (another LLM) assesses whether the target LLM's response constitutes a successful jailbreak based on a 0-10 compliance scale.
* **Interactive Web UI:** A [Streamlit](https://streamlit.io/) interface allows users to configure models, manage tasks/strategies, run tests, view real-time progress, and download results.
* **Customizable & Evolvable Strategies:** Easily define new tasks and attack strategies via JSON files or the UI. The evolutionary mode can combine existing strategies to create new, more effective ones automatically.
* **Comprehensive Logging:** Records detailed information about each test attempt to a `results/jailbreak_log.jsonl` file.

---
## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python:** Version 3.8 or higher.
2.  **Ollama:** Installed and running. Download from [ollama.com](https://ollama.com/).
3.  **Ollama Models:** Download the LLMs you intend to use. For example:
    ```bash
    ollama pull qwen2:7b
    ```

---
## Setup and Installation

1.  **Clone or Download the Repository.**
2.  **Windows Users:** Run `run_app.bat`. It creates a virtual environment, installs dependencies, and starts the app.
3.  **Manual Setup (All Platforms):**
    ```bash
    # Navigate to the project directory
    python -m venv ashkit_env
    # Activate the environment (Win: ashkit_env\Scripts\activate | macOS/Linux: source ashkit_env/bin/activate)
    pip install -r requirements.txt
    streamlit run app.py
    ```

---
## How to Use

1.  **Start the Application:** Run the app using the script or manual commands. It should open at `http://localhost:8501`.

2.  **Configure Models (Sidebar):** Set the Ollama model names for the Target, Judge, and Crafter.

3.  **Select a Mode:**
    * **Model Profiling Tab:**
        * Click "Start Full Model Profile" to run all tasks against all strategies.
        * Observe the progress and view the visualizations (effectiveness per strategy, vulnerability per task, and a heatmap) update in real-time.
    * **Evolutionary Simulation Tab:**
        * Select a single task you want to accomplish from the dropdown and configure the pool size.
        * Click "Start Simulation".
        * The tool will evolve strategies over generations. New, combined strategies may be created automatically.
        * The final output will list the most successful, stable "solution" prompts found during the simulation.

4.  **Manage Data (Sidebar):** Navigate to the "Manage Data" page to add, edit, or delete the tasks and strategies used in the tests. You can also manually combine strategies here.

5.  **View Logs & Results:** A table of all historical results is available at the bottom of the Red Teaming page, which can be refreshed from the log file and downloaded as a CSV.

---
## Directory Structure
```
AshKit/
├── app.py                  # Streamlit UI application
├── evolutionary_runner.py  # Logic for Evolutionary Simulation mode
├── graph_runner.py         # Core LangGraph execution logic
├── langgraph_setup.py      # LangGraph definition
├── llm_interface.py        # Ollama interaction functions
├── judge.py                # AI Judge logic
├── visuals.py              # Visualization functions
├── utils.py                # Utility functions (data loading, etc.)
├── management_page.py      # UI for managing tasks/strategies
├── requirements.txt        # Python dependencies
├── run_app.bat             # Windows startup script
├── README.md               # This file
├── data/
│   ├── tasks.json
│   └── strategies.json
└── results/
└── jailbreak_log.jsonl