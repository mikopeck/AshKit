# app.py
import streamlit as st
import time

from utils import load_tasks, load_strategies, load_results_log, append_results_to_log, add_strategy
from graph_runner import run_single_jailbreak_attempt
import evolutionary_runner
from visuals import update_visuals
from management_page import render_management_page

st.set_page_config(layout="wide", page_title="AshKit")

st.title("🔥 AshKit: LLM Red Teaming Toolkit")
st.caption("A workbench for red teaming LLMs with two modes: broad model profiling and a strategy discovery engine.")

# --- Session State & Callbacks ---
if 'tasks' not in st.session_state: st.session_state.tasks = load_tasks()
if 'strategies' not in st.session_state: st.session_state.strategies = load_strategies()
if 'results' not in st.session_state: st.session_state.results = load_results_log("results/jailbreak_log.jsonl")
if 'simulation' not in st.session_state: st.session_state.simulation = evolutionary_runner.initialize_simulation_state()
if 'stop_run' not in st.session_state: st.session_state.stop_run = False
if 'profiling_in_progress' not in st.session_state: st.session_state.profiling_in_progress = False

def stop_profiling_callback():
    """Stops the profiling run."""
    st.session_state.stop_run = True
    st.session_state.profiling_in_progress = False
    st.warning("Profiling run stopped by user.")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Core Configuration")
    crafter_model_name = st.text_input("Crafter Model", value="qwen3:8b")
    target_model_name = st.text_input("Target Model", value="qwen3:8b")
    judge_model_name = st.text_input("Judge Model", value="qwen3:8b")
    st.markdown("---")
    
    page = st.selectbox("Navigation", ["🔥 Red Teaming", "🗂️ Manage Data"])
    st.markdown("---")
    st.info("AshKit is an open-source tool for LLM vulnerability research. Use it ethically and responsibly.")

# --- Page Routing ---
if page == "🔥 Red Teaming":
    profiling_tab, attack_tab = st.tabs(["📊 Model Profiling", "🧬 Strategy Discovery Engine"])

    with profiling_tab:
        st.subheader("Profile a model's vulnerabilities across all tasks and strategies.")
        
        # --- PROFILING CONTROLS ---
        if st.session_state.profiling_in_progress:
            if st.button("Stop Current Run", type="primary", on_click=stop_profiling_callback, use_container_width=True):
                st.rerun()
        else:
            if st.session_state.simulation.get('is_running'):
                st.warning("Cannot start profiling while the discovery engine is running.")
            
            if st.button("Start Full Model Profile", type="secondary", use_container_width=True, disabled=st.session_state.simulation.get('is_running')):
                st.session_state.profiling_in_progress = True
                st.session_state.stop_run = False
                st.rerun()

        # --- VISUALS & LOGS DISPLAY (PERSISTENT) ---
        visuals_placeholder = st.empty()
        if st.session_state.results:
            update_visuals(visuals_placeholder, st.session_state.results)
        else:
            with visuals_placeholder.container():
                st.info("No results yet. Run a test to generate data.")

        # --- PROFILING EXECUTION LOGIC ---
        if st.session_state.profiling_in_progress:
            tasks_to_run = st.session_state.tasks
            strategies_to_apply = st.session_state.strategies
            total_runs = len(tasks_to_run) * len(strategies_to_apply)
            progress_bar = st.progress(0, text="Starting profiling run...")
            live_monitor_container = st.container(border=True)
            
            for i, task in enumerate(tasks_to_run):
                if st.session_state.stop_run: break
                for j, strategy in enumerate(strategies_to_apply):
                    if st.session_state.stop_run: break
                    
                    current_run_num = (i * len(strategies_to_apply)) + j + 1
                    progress_text = f"Running {current_run_num}/{total_runs}: Task '{task['id']}' | Strategy '{strategy['name']}'"
                    progress_bar.progress(current_run_num / total_runs, text=progress_text)
                    
                    with live_monitor_container:
                        st.markdown(f"--- \n#### 🏃‍♂️ Running Test {current_run_num}/{total_runs}")
                        ui_placeholders = {"crafter_status": st.empty(), "prompt_display": st.empty(), "target_status": st.empty(), "response_display": st.empty(), "judge_status": st.empty(), "verdict_display": st.empty()}
                        
                        result = run_single_jailbreak_attempt(
                            task=task, 
                            strategy=strategy, 
                            target_model_name=target_model_name, 
                            judge_model_name=judge_model_name, 
                            crafter_model_name=crafter_model_name, 
                            ui_placeholders=ui_placeholders
                        )
                        
                        append_results_to_log([result], "results/jailbreak_log.jsonl")
                        st.session_state.results.insert(0, result)
                        
                        update_visuals(visuals_placeholder, st.session_state.results)

            if not st.session_state.stop_run:
                progress_bar.progress(1.0, "Profiling run completed!")
                st.balloons()
            
            st.session_state.profiling_in_progress = False
            st.session_state.stop_run = False
            st.rerun()

    with attack_tab:
        st.subheader("Evolve and discover new jailbreak strategies.")
        st.info("This engine eliminates failing strategies (0-2 score) and evolves new ones from the entire history of attempts. High-performing new strategies (8+ score) are automatically saved.")

        is_sim_running = st.session_state.simulation.get('is_running', False)
        is_sim_paused = st.session_state.simulation.get('is_paused', False)
        is_sim_active = is_sim_running or is_sim_paused

        # --- SIMULATION CONFIGURATION ---
        sim_cfg_col1, sim_cfg_col2 = st.columns([2, 1])
        with sim_cfg_col1:
            selected_task_id = st.selectbox(
                "Select a Single Task:", 
                [t['id'] for t in st.session_state.tasks], 
                disabled=is_sim_active, 
                help="Choose the goal for the attack."
            )
        with sim_cfg_col2:
            pool_size = st.number_input(
                "Pool Size per Generation", 
                min_value=2, max_value=100, value=14, 
                disabled=is_sim_active,
                help="The engine will evolve new strategies if the active pool is smaller than this."
            )

        # --- PAUSE/RESUME/STOP CONTROLS ---
        st.markdown("---")
        ctrl_cols = st.columns(3)
        if not is_sim_active:
            if ctrl_cols[0].button("▶️ Start Discovery", use_container_width=True, type="primary"):
                model_config = {"target_model_name": target_model_name, "judge_model_name": judge_model_name, "crafter_model_name": crafter_model_name}
                task_to_run = next((t for t in st.session_state.tasks if t['id'] == selected_task_id), None)
                st.session_state.simulation = evolutionary_runner.initialize_simulation_state(
                    pool_size=pool_size,
                    strategies=st.session_state.strategies,
                    task=task_to_run,
                    model_config=model_config
                )
                st.session_state.simulation['is_running'] = True
                st.rerun()
        
        if is_sim_running:
            if ctrl_cols[0].button("⏸️ Pause", use_container_width=True):
                st.session_state.simulation['is_running'] = False
                st.session_state.simulation['is_paused'] = True
                st.rerun()

        if is_sim_paused:
            if ctrl_cols[0].button("▶️ Resume", use_container_width=True, type="primary"):
                st.session_state.simulation['is_running'] = True
                st.session_state.simulation['is_paused'] = False
                st.rerun()
        
        if is_sim_active:
            if ctrl_cols[2].button("⏹️ Stop & Reset", use_container_width=True):
                st.session_state.simulation = evolutionary_runner.initialize_simulation_state()
                st.session_state.strategies = load_strategies()
                st.warning("Discovery engine stopped and reset by user.")
                st.rerun()

        st.markdown("---")

        # --- UNIFIED SIMULATION DISPLAY & EXECUTION LOGIC ---
        if st.session_state.simulation.get('task'):
            
            status_container = st.container()

            live_display_container = st.container(border=True)
            with live_display_container:
                progress_text_ph = st.empty()
                progress_bar_ph = st.empty()
                live_cols = st.columns(3)
                avg_score_ph = live_cols[0].empty()
                top_score_ph = live_cols[1].empty()
                success_rate_ph = live_cols[2].empty()

            overall_stat_cols = st.columns(3)
            overall_stat_cols[0].metric("Current Generation", st.session_state.simulation['generation'])
            overall_stat_cols[1].metric("Solutions Found", f"{len(st.session_state.simulation.get('solutions', []))} / {st.session_state.simulation.get('solutions_to_find', 3)}")
            active_strats = sum(1 for s in st.session_state.simulation.get('strategy_status', {}).values() if s['status'] == 'active')
            overall_stat_cols[2].metric("Active Strategies", active_strats)

            res_col, strat_col = st.columns([3, 2])
            
            if st.session_state.simulation.get('is_running'):
                sim_state = st.session_state.simulation
                all_strategies = st.session_state.strategies

                ui_placeholders = {
                    "progress_text": progress_text_ph,
                    "progress_bar": progress_bar_ph,
                    "avg_score": avg_score_ph,
                    "top_score": top_score_ph,
                    "success_rate": success_rate_ph
                }

                new_state, new_results, newly_saved = evolutionary_runner.run_one_generation(sim_state, all_strategies, ui_placeholders)

                st.session_state.simulation = new_state
                
                # The logic for appending new strategies is now correctly handled inside the runner.
                # No action is needed here, preventing the old bug.

                if new_results:
                    append_results_to_log(new_results, "results/jailbreak_log.jsonl")
                    st.session_state.results = load_results_log("results/jailbreak_log.jsonl")

                if len(st.session_state.simulation.get('solutions', [])) >= st.session_state.simulation.get('solutions_to_find', 3):
                    st.session_state.simulation['is_running'] = False
                    st.session_state.simulation['is_paused'] = True
                    st.toast("Target number of solutions found. Pausing.")

                time.sleep(1) 
                st.rerun()

elif page == "🗂️ Manage Data":
    render_management_page(crafter_model_name)