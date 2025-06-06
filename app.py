# app.py
import streamlit as st
import pandas as pd
import uuid
import json

from utils import load_tasks, load_strategies, load_results_log, append_results_to_log
from graph_runner import run_single_jailbreak_attempt
import evolutionary_runner
from visuals import update_visuals
from management_page import render_management_page

st.set_page_config(layout="wide", page_title="AshKit")

st.title("🔥 AshKit: LLM Red Teaming Toolkit")
st.caption("A workbench for red teaming LLMs with two modes: broad model profiling and an evolutionary attack simulator.")

# --- Session State & Callbacks ---
if 'tasks' not in st.session_state: st.session_state.tasks = load_tasks()
if 'strategies' not in st.session_state: st.session_state.strategies = load_strategies()
if 'results' not in st.session_state: st.session_state.results = load_results_log("results/jailbreak_log.jsonl")
if 'simulation' not in st.session_state: st.session_state.simulation = evolutionary_runner.initialize_simulation_state()
if 'stop_run' not in st.session_state: st.session_state.stop_run = False

def stop_button_callback():
    st.session_state.stop_run = True
    if st.session_state.simulation['is_running']:
        st.session_state.simulation['is_running'] = False
        st.warning("Evolutionary simulation stopped by user.")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Core Configuration")
    crafter_model_name = st.text_input("Crafter Model", value="qwen3:8b")
    target_model_name = st.text_input("Target Model", value="qwen3:8b")
    judge_model_name = st.text_input("Judge Model", value="qwen3:8b")
    st.markdown("---")
    
    page = st.radio("Navigation", ["🔥 Red Teaming", "🗂️ Manage Data"])
    st.markdown("---")
    st.info("AshKit is an open-source tool for LLM vulnerability research. Use it ethically and responsibly.")

# --- Page Routing ---
if page == "🔥 Red Teaming":
    profiling_tab, attack_tab = st.tabs(["📊 Model Profiling", "🧬 Evolutionary Simulation"])

    with profiling_tab:
        st.subheader("Profile a model's vulnerabilities across all tasks and strategies.")
        
        if st.session_state.simulation['is_running']:
            st.warning("Cannot start profiling while the evolutionary simulation is running.")

        if st.button("Stop Current Run", type="primary", on_click=stop_button_callback, use_container_width=True, key="stop_profiling_run"):
             st.session_state.stop_run = True

        visuals_placeholder = st.empty()

        if st.button("Start Full Model Profile", type="secondary", use_container_width=True, disabled=st.session_state.simulation['is_running']):
            st.session_state.stop_run = False
            tasks_to_run = st.session_state.tasks
            strategies_to_apply = st.session_state.strategies
            total_runs = len(tasks_to_run) * len(strategies_to_apply)
            progress_bar = st.progress(0, text="Starting profiling run...")
            live_monitor_container = st.container(border=True)
            run_results = []
            for i, task in enumerate(tasks_to_run):
                if st.session_state.stop_run: break
                for j, strategy in enumerate(strategies_to_apply):
                    if st.session_state.stop_run: break
                    current_run_num = (i * len(strategies_to_apply)) + j + 1
                    progress_bar.progress(current_run_num / total_runs, text=f"Running {current_run_num}/{total_runs}: Task '{task['id']}' | Strategy '{strategy['name']}'")
                    with live_monitor_container:
                        st.markdown(f"--- \n#### 🔬 Running Test {current_run_num}/{total_runs}")
                        ui_placeholders = {"crafter_status": st.empty(), "prompt_display": st.empty(), "target_status": st.empty(), "response_display": st.empty(), "judge_status": st.empty(), "verdict_display": st.empty()}
                        result = run_single_jailbreak_attempt(task=task, strategy=strategy, target_model_name=target_model_name, judge_model_name=judge_model_name, crafter_model_name=crafter_model_name, ui_placeholders=ui_placeholders)
                        run_results.append(result)
                        st.session_state.results.insert(0, result)
                        update_visuals(visuals_placeholder, st.session_state.results)
            
            if st.session_state.stop_run: 
                st.warning("Run stopped by user.")
            else:
                progress_bar.progress(1.0, "Profiling run completed!")
                st.balloons()
            st.session_state.stop_run = False
            st.rerun()

    with attack_tab:
        st.subheader("Evolve the best jailbreak for a single task.")
        st.info("This mode uses a genetic algorithm to breed and refine strategies over multiple generations. Every 3 generations, it will attempt to combine the top 2 strategies into a new, hybrid one.")

        # --- SIMULATION CONFIGURATION ---
        sim_cfg_col1, sim_cfg_col2 = st.columns([2, 1])
        with sim_cfg_col1:
            selected_task_id = st.selectbox(
                "Select a Single Task:", 
                [t['id'] for t in st.session_state.tasks], 
                disabled=st.session_state.simulation['is_running'], 
                help="Choose the goal for the attack."
            )
        with sim_cfg_col2:
            pool_size = st.number_input(
                "Pool Size per Generation", 
                min_value=2, max_value=100, value=20, 
                disabled=st.session_state.simulation['is_running'],
                help="Number of jailbreaks to generate and test in each generation."
            )

        # --- SIMULATION CONTROLS ---
        sim_control_col1, sim_control_col2, sim_control_col3 = st.columns(3)
        if not st.session_state.simulation['is_running'] and not st.session_state.simulation['is_paused']:
            if sim_control_col1.button("▶️ Start Simulation", use_container_width=True, type="primary"):
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
        
        if st.session_state.simulation['is_paused']:
            if sim_control_col1.button("▶️ Resume Simulation", use_container_width=True, type="primary"):
                st.session_state.simulation['is_running'] = True
                st.session_state.simulation['is_paused'] = False
                st.rerun()

        if st.session_state.simulation['is_running'] or st.session_state.simulation['is_paused']:
            if sim_control_col2.button("⏹️ Stop Simulation", use_container_width=True):
                st.session_state.simulation['is_running'] = False
                st.session_state.simulation['is_paused'] = False
                st.warning("Simulation stopped by user.")
                st.rerun()
            if sim_control_col3.button("🔄 Reset Simulation", use_container_width=True):
                st.session_state.simulation = evolutionary_runner.initialize_simulation_state()
                st.session_state.strategies = load_strategies() # Reload original strategies
                st.info("Simulation has been reset.")
                st.rerun()

        st.markdown("---")

        # --- SIMULATION RUNNING LOGIC & DISPLAY ---
        if st.session_state.simulation['is_running'] and not st.session_state.simulation['is_paused']:
            live_monitor = st.container(border=True)
            with live_monitor:
                st.subheader(f"🧬 Running Generation {st.session_state.simulation['generation'] + 1}")
                progress_text_placeholder = st.empty()
                progress_bar_placeholder = st.empty()
                live_stats_cols = st.columns(3)
                avg_score_placeholder = live_stats_cols[0].empty()
                top_score_placeholder = live_stats_cols[1].empty()
                success_rate_placeholder = live_stats_cols[2].empty()

            ui_placeholders = {
                "progress_text": progress_text_placeholder,
                "progress_bar": progress_bar_placeholder,
                "avg_score": avg_score_placeholder,
                "top_score": top_score_placeholder,
                "success_rate": success_rate_placeholder,
            }

            new_state, new_results, new_strategy = evolutionary_runner.run_one_generation(
                st.session_state.simulation, 
                st.session_state.strategies,
                ui_placeholders
            )
            st.session_state.simulation = new_state
            
            if new_strategy:
                st.session_state.strategies.append(new_strategy)
                st.toast(f"✨ New strategy evolved: '{new_strategy['name']}'!", icon="🧬")

            if new_results:
                append_results_to_log(new_results, "results/jailbreak_log.jsonl")
                st.session_state.results.extend(new_results)
                st.session_state.results = sorted(st.session_state.results, key=lambda x: x.get("timestamp", ""), reverse=True)
            
            if len(st.session_state.simulation.get("solutions", [])) >= 3:
                st.session_state.simulation['is_paused'] = True
                st.session_state.simulation['is_running'] = False
                st.success("Simulation paused: Found 3 solutions!")
            
            live_monitor.empty()
            st.rerun()

        # --- DISPLAY SIMULATION STATE ---
        if st.session_state.simulation.get('task'):
            st.header(f"📊 Live Simulation Status for Task: `{st.session_state.simulation['task']['id']}`")
            if st.session_state.simulation['is_paused']:
                st.success("Simulation Paused")

            stat_cols = st.columns(3)
            stat_cols[0].metric("Current Generation", st.session_state.simulation['generation'])
            stat_cols[1].metric("Solutions Found", f"{len(st.session_state.simulation.get('solutions', []))} / 3")
            stat_cols[2].metric("Elites from Last Gen", len(st.session_state.simulation.get('elites', [])))

            res_col, strat_col = st.columns([3, 2])

            with res_col:
                st.subheader("🔍 Current Generation Results")
                if st.session_state.simulation.get('current_pool'):
                    df_pool = pd.DataFrame(st.session_state.simulation['current_pool'])
                    st.dataframe(df_pool[['strategy_name', 'final_rating', 'crafted_jailbreak_prompt']], use_container_width=True, height=300)
                else:
                    st.info("Waiting to start simulation...")

            with strat_col:
                st.subheader("📈 Strategy Weights")
                if st.session_state.simulation.get('strategy_weights'):
                    weights = st.session_state.simulation['strategy_weights']
                    # Display only strategies that are in the current session_state
                    active_strategies = {s['id']: s['name'] for s in st.session_state.strategies}
                    df_weights_data = {
                        "Strategy": [active_strategies.get(sid, sid) for sid in weights.keys() if sid in active_strategies],
                        "Weight": [w for sid, w in weights.items() if sid in active_strategies]
                    }
                    df_weights = pd.DataFrame(df_weights_data).set_index('Strategy')
                    st.bar_chart(df_weights)
                else:
                    st.info("Weights will appear after the first generation.")

            st.subheader("🏆 Found Solutions")
            if st.session_state.simulation.get('solutions'):
                for i, sol in enumerate(st.session_state.simulation['solutions']):
                    with st.expander(f"**Solution {i+1}** (Found in Gen {sol.get('generation_found')}) - Strategy: `{sol.get('strategy_name')}`"):
                        st.markdown("**Winning Jailbreak Prompt:**")
                        st.code(sol.get("crafted_jailbreak_prompt"), language=None)
                        st.markdown("**🎯 Target's Response:**")
                        st.markdown(sol.get("target_llm_response", "No response recorded."))
                        st.markdown(f"**⚖️ Judge's Verdict:** {sol.get('final_rating')}/10 - *{sol.get('verdict_reasoning')}*")
            else:
                st.info("Solutions that achieve a perfect score three times will be listed here.")


    st.markdown("---")
    st.header("📜 Test Logs & Visualizations")
    visuals_placeholder_main = st.empty()
    update_visuals(visuals_placeholder_main, st.session_state.results)
    if st.button("Refresh Results from Log File"):
        st.session_state.results = load_results_log("results/jailbreak_log.jsonl")
        st.rerun()
    if st.session_state.results:
        st.subheader("All Test Run Logs")
        df_results = pd.DataFrame(st.session_state.results)
        st.dataframe(df_results, use_container_width=True)
        csv = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download Results as CSV", data=csv, file_name='ashkit_results.csv', mime='text/csv')
    else:
        st.info("No results yet. Run a test to see results.")

elif page == "🗂️ Manage Data":
    render_management_page(crafter_model_name)