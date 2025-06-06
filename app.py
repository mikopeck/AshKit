# app.py
import streamlit as st
import pandas as pd
import uuid
import json

from utils import load_tasks, load_strategies, load_results_log, append_results_to_log
from graph_runner import run_single_jailbreak_attempt
import comprehensive_runner
from visuals import update_visuals
from management_page import render_management_page

st.set_page_config(layout="wide", page_title="AshKit")

st.title("🔬 AshKit: LLM Red Teaming Toolkit")
st.caption("A workbench for red teaming LLMs with two modes: broad model profiling and focused attacks.")

# --- Session State & Callbacks ---
if 'tasks' not in st.session_state: st.session_state.tasks = load_tasks()
if 'strategies' not in st.session_state: st.session_state.strategies = load_strategies()
if 'results' not in st.session_state: st.session_state.results = load_results_log("results/jailbreak_log.jsonl")
if 'running_test' not in st.session_state: st.session_state.running_test = False
if 'stop_run' not in st.session_state: st.session_state.stop_run = False

def stop_button_callback():
    st.session_state.stop_run = True

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
    st.header("🚀 Select a Mode")

    if st.session_state.running_test:
        st.button("🛑 Stop Run", type="primary", on_click=stop_button_callback, use_container_width=True)

    profiling_tab, attack_tab = st.tabs(["📊 Model Profiling", "🎯 Task-Focused Attack"])

    with profiling_tab:
        st.subheader("Profile a model's vulnerabilities across all tasks and strategies.")
        visuals_placeholder = st.empty()

        if st.button("Start Full Model Profile", type="secondary", use_container_width=True, disabled=st.session_state.running_test):
            st.session_state.running_test = True
            st.session_state.stop_run = False
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
                    progress_bar.progress(current_run_num / total_runs, text=f"Running {current_run_num}/{total_runs}: Task '{task['id']}' | Strategy '{strategy['name']}'")
                    with live_monitor_container:
                        st.markdown(f"--- \n#### 🔬 Running Test {current_run_num}/{total_runs}")
                        ui_placeholders = {"crafter_status": st.empty(), "prompt_display": st.empty(), "target_status": st.empty(), "response_display": st.empty(), "judge_status": st.empty(), "verdict_display": st.empty()}
                        result = run_single_jailbreak_attempt(task=task, strategy=strategy, target_model_name=target_model_name, judge_model_name=judge_model_name, crafter_model_name=crafter_model_name, ui_placeholders=ui_placeholders)
                        st.session_state.results.insert(0, result)
                        update_visuals(visuals_placeholder, st.session_state.results)
            if st.session_state.stop_run: st.warning("Run stopped by user.")
            else:
                progress_bar.progress(1.0, "Profiling run completed!")
                st.balloons()
            st.session_state.running_test = False
            st.rerun()

    with attack_tab:
        st.subheader("Find the best jailbreak for a single task.")
        st.info("This mode runs all strategies, then combines the most effective ones to find the best attack.")
        selected_task_id = st.selectbox("Select a Single Task:", [t['id'] for t in st.session_state.tasks], disabled=st.session_state.running_test, help="Choose the goal for the attack.")
        if st.button("Launch Task-Focused Attack", type="secondary", use_container_width=True, disabled=st.session_state.running_test):
            st.session_state.running_test = True
            st.session_state.stop_run = False
            task_to_run = next((t for t in st.session_state.tasks if t['id'] == selected_task_id), None)
            model_config = {"target_model_name": target_model_name, "judge_model_name": judge_model_name, "crafter_model_name": crafter_model_name}
            attack_status_container = st.container(border=True)
            with attack_status_container:
                st.subheader("🔴 Live Attack Monitor")
                log_placeholder = st.empty()
                detail_container = st.container(border=True)
                with detail_container:
                    ui_placeholders = { "crafter_status": st.empty(), "prompt_display": st.empty(), "target_status": st.empty(), "response_display": st.empty(), "judge_status": st.empty(), "verdict_display": st.empty() }
            initial_state = comprehensive_runner.ComprehensiveRunState(task=task_to_run, all_strategies=st.session_state.strategies, model_config=model_config, ui_monitor_placeholders=ui_placeholders, log_placeholder=log_placeholder, was_stopped=False, run_log=[], probing_results=[], top_4_strategies=[], strategy_combinations=[], combined_prompts=[], final_assault_results=[])
            with st.spinner("Task-focused attack in progress..."):
                final_state = comprehensive_runner.comprehensive_graph.invoke(initial_state)
            if final_state.get("was_stopped"): st.warning("Attack was stopped by the user.")
            else: st.success("Task-Focused Attack Finished!")
            all_new_results = final_state.get("probing_results", []) + final_state.get("final_assault_results", [])
            if all_new_results:
                append_results_to_log(all_new_results, "results/jailbreak_log.jsonl")
            st.session_state.results.extend(all_new_results)
            st.session_state.results = sorted(st.session_state.results, key=lambda x: x.get("timestamp", ""), reverse=True)
            if all_new_results:
                successful_results = [r for r in all_new_results if r.get("final_rating", -1) > 0]
                if successful_results:
                    best_result = max(successful_results, key=lambda x: x.get("final_rating", -1))
                    st.markdown("---")
                    st.header("🏆 Most Effective Attack Found")
                    st.subheader(f"Strategy: `{best_result.get('strategy_name', 'N/A')}` | Final Rating: `{best_result.get('final_rating')}/10`")
                    with st.container(border=True):
                        st.markdown("**Winning Jailbreak Prompt:**")
                        st.code(best_result.get("crafted_jailbreak_prompt"), language=None)
                    if best_result.get("creator_prompt_for_combination"):
                        with st.expander("See how this prompt was created (Instructions for Combination Crafter)"):
                            st.code(best_result.get("creator_prompt_for_combination"), language='text')
                    with st.container(border=True):
                        st.markdown("**🎯 Target's Response:**")
                        st.markdown(best_result.get("target_llm_response", "No response recorded."))
                    with st.container(border=True):
                        st.markdown("**⚖️ Judge's Verdict:**")
                        st.markdown(f"**Rating:** {best_result.get('final_rating')}/10")
                        st.markdown(f"**Reasoning:** {best_result.get('verdict_reasoning')}")
                else: st.warning("No successful jailbreak was found for this task in this run.")
            st.session_state.running_test = False
            st.rerun()

    st.markdown("---")
    st.header("📊 Test Logs & Visualizations")
    visuals_placeholder_main = st.empty()
    if not st.session_state.running_test:
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