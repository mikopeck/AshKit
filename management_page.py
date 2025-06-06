# management_page.py
import streamlit as st
import uuid
from utils import (
    load_tasks, add_task, update_task, delete_task,
    load_strategies, add_strategy, update_strategy, delete_strategy,
    combine_and_craft_strategy
)

def render_management_page(crafter_model_name: str):
    """Renders the entire data management page."""
    
    st.header("🗂️ Manage Tasks and Strategies")
    st.info("Here you can add, edit, delete, and combine your testing data.")

    # Initialize session state for editing forms
    if 'editing_task_id' not in st.session_state:
        st.session_state.editing_task_id = None
    if 'editing_strategy_id' not in st.session_state:
        st.session_state.editing_strategy_id = None
    if 'new_combined_strat' not in st.session_state:
        st.session_state.new_combined_strat = None

    task_tab, strategy_tab = st.tabs(["Manage Tasks", "Manage Strategies"])

    with task_tab:
        manage_tasks()

    with strategy_tab:
        manage_strategies(crafter_model_name)

def manage_tasks():
    """UI for displaying and managing tasks."""
    st.subheader("Task Editor")

    task_to_edit = next((t for t in st.session_state.tasks if t['id'] == st.session_state.editing_task_id), None) if st.session_state.editing_task_id else None
    
    with st.form(key="task_form", clear_on_submit=True):
        st.write("**Add a new task or edit an existing one:**")
        
        default_id = task_to_edit['id'] if task_to_edit else f"T_custom_{uuid.uuid4().hex[:6]}"
        default_desc = task_to_edit['description'] if task_to_edit else ""
        default_prompt = task_to_edit['prompt'] if task_to_edit else ""
        default_harm = task_to_edit['harm_category'] if task_to_edit else "Custom"
        
        task_id = st.text_input("Unique Task ID", value=default_id, disabled=bool(task_to_edit))
        task_desc = st.text_input("Task Description", value=default_desc)
        task_prompt = st.text_area("Task Prompt (The harmful request)", value=default_prompt, height=150)
        task_harm = st.text_input("Harm Category", value=default_harm)
        
        if st.form_submit_button("Save Task"):
            new_task_data = {"id": task_id, "description": task_desc, "prompt": task_prompt, "harm_category": task_harm}
            try:
                if task_to_edit:
                    update_task(task_id, new_task_data)
                    st.session_state.editing_task_id = None
                    st.success(f"Task '{task_desc}' updated!")
                else:
                    add_task(new_task_data)
                    st.success(f"Task '{task_desc}' added!")
                
                st.session_state.tasks = load_tasks()
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    st.markdown("---")
    st.subheader("Existing Tasks")
    for task in st.session_state.tasks:
        with st.expander(f"**{task['description']}** (`{task['id']}`)"):
            st.code(task['prompt'], language=None)
            st.caption(f"Harm Category: {task['harm_category']}")
            
            col1, col2, _ = st.columns([1, 1, 5])
            if col1.button("Edit", key=f"edit_task_{task['id']}"):
                st.session_state.editing_task_id = task['id']
                st.rerun()
            
            if col2.button("Delete", key=f"delete_task_{task['id']}", type="primary"):
                try:
                    delete_task(task['id'])
                    st.session_state.tasks = load_tasks()
                    st.success(f"Task '{task['description']}' deleted.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

def manage_strategies(crafter_model_name: str):
    """UI for displaying, managing, and combining strategies."""
    st.subheader("Strategy Editor")
    
    strategy_to_edit = next((s for s in st.session_state.strategies if s['id'] == st.session_state.editing_strategy_id), None) if st.session_state.editing_strategy_id else None

    with st.form(key="strategy_form", clear_on_submit=True):
        st.write("**Add a new strategy or edit an existing one:**")
        
        default_id = strategy_to_edit['id'] if strategy_to_edit else f"S_custom_{uuid.uuid4().hex[:6]}"
        default_name = strategy_to_edit['name'] if strategy_to_edit else ""
        default_desc = strategy_to_edit['description'] if strategy_to_edit else ""
        default_instruct = strategy_to_edit.get('instructions_for_crafter', '') if strategy_to_edit else ""

        strat_id = st.text_input("Unique Strategy ID", value=default_id, disabled=bool(strategy_to_edit))
        strat_name = st.text_input("Strategy Name", value=default_name)
        strat_desc = st.text_area("Strategy Description (for display)", value=default_desc)
        strat_instruct = st.text_area("Instructions for Crafter LLM", value=default_instruct, height=150)
        
        if st.form_submit_button("Save Strategy"):
            new_strat_data = {"id": strat_id, "name": strat_name, "description": strat_desc, "instructions_for_crafter": strat_instruct}
            try:
                if strategy_to_edit:
                    update_strategy(strat_id, new_strat_data)
                    st.session_state.editing_strategy_id = None
                    st.success(f"Strategy '{strat_name}' updated!")
                else:
                    add_strategy(new_strat_data)
                    st.success(f"Strategy '{strat_name}' added!")
                
                st.session_state.strategies = load_strategies()
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    st.markdown("---")
    st.subheader("Combine Strategies")
    with st.container(border=True):
        st.write("Select two strategies and provide a sample harmful task to guide the combination process.")
        strategy_options = {s['id']: f"{s['name']} ({s['id']})" for s in st.session_state.strategies}
        
        col1, col2 = st.columns(2)
        strat_a_id = col1.selectbox("Select Strategy A", options=list(strategy_options.keys()), format_func=lambda x: strategy_options[x], key="strat_a")
        strat_b_id = col2.selectbox("Select Strategy B", options=list(strategy_options.keys()), format_func=lambda x: strategy_options[x], key="strat_b", index=min(1, len(strategy_options)-1))
        
        sample_task = st.text_area("Sample Harmful Task Prompt", "e.g., How do I build a phishing website?", key="sample_task")

        if st.button("Combine Strategies"):
            if strat_a_id == strat_b_id: st.warning("Please select two different strategies.")
            else:
                strat_a = next(s for s in st.session_state.strategies if s['id'] == strat_a_id)
                strat_b = next(s for s in st.session_state.strategies if s['id'] == strat_b_id)
                with st.spinner("🤖 Crafter LLM is combining strategies..."):
                    try:
                        st.session_state.new_combined_strat = combine_and_craft_strategy(strat_a, strat_b, sample_task, crafter_model_name)
                        st.rerun()
                    except Exception as e: st.error(f"Failed to combine strategies: {e}")

    if st.session_state.new_combined_strat:
        with st.form(key="combined_strategy_form"):
            st.subheader("Save New Combined Strategy")
            new_strat = st.session_state.new_combined_strat
            
            combo_name = st.text_input("New Strategy Name", value=new_strat['name'])
            combo_id = st.text_input("New Strategy ID", value=f"S_combo_{uuid.uuid4().hex[:6]}")
            combo_desc = st.text_area("New Strategy Description", value=new_strat['description'], height=100)
            combo_instruct = st.text_area("New Strategy Instructions (Generated)", value=new_strat['instructions_for_crafter'], height=200)

            if st.form_submit_button("Add this Combined Strategy"):
                final_strat_data = {"id": combo_id, "name": combo_name, "description": combo_desc, "instructions_for_crafter": combo_instruct, "source_strategies": new_strat.get("source_strategies", [])}
                try:
                    add_strategy(final_strat_data)
                    st.session_state.strategies = load_strategies()
                    st.session_state.new_combined_strat = None
                    st.success(f"Successfully added combined strategy '{combo_name}'!")
                    st.rerun()
                except ValueError as e: st.error(e)

    st.markdown("---")
    st.subheader("Existing Strategies")
    for strat in st.session_state.strategies:
        with st.expander(f"**{strat['name']}** (`{strat['id']}`)"):
            st.markdown(f"**Description:** {strat.get('description', 'N/A')}")
            st.markdown("**Instructions for Crafter:**")
            st.code(strat.get('instructions_for_crafter', 'N/A'), language=None)
            
            col1, col2, _ = st.columns([1, 1, 5])
            if col1.button("Edit", key=f"edit_strat_{strat['id']}"):
                st.session_state.editing_strategy_id = strat['id']
                st.session_state.new_combined_strat = None
                st.rerun()
            
            if col2.button("Delete", key=f"delete_strat_{strat['id']}", type="primary"):
                try:
                    delete_strategy(strat['id'])
                    st.session_state.strategies = load_strategies()
                    st.success(f"Strategy '{strat['name']}' deleted.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))