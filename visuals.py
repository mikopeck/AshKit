# visuals.py
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def update_visuals(placeholder: Any, results_data: List[Dict[str, Any]]):
    """
    Clears a placeholder (created with st.empty()) and redraws all result 
    visualizations inside it.
    """
    if not results_data:
        with placeholder.container():
            st.info("No results yet. Run a test to generate data.")
        return

    # Use the placeholder.container() context to replace the content of the st.empty() element
    with placeholder.container():
        df_results = pd.DataFrame(results_data)
        
        # Ensure the rating column exists and is numeric
        if 'final_rating' not in df_results.columns:
            df_results['final_rating'] = -1
        df_results['final_rating'] = pd.to_numeric(df_results['final_rating'], errors='coerce').fillna(-1).astype(int)

        # Filter out results with errors (-1 rating) for meaningful visualizations
        df_viz = df_results[df_results['final_rating'] != -1].copy()

        if df_viz.empty:
            st.info("Waiting for the first valid (non-error) result to generate plots...")
            return

        st.markdown("---")
        st.header("📊 Live Results Visualizations")
        
        # --- The Visuals ---
        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            st.subheader("Effectiveness per Strategy")
            if 'strategy_name' in df_viz.columns and not df_viz['strategy_name'].empty:
                strategy_effectiveness = df_viz.groupby('strategy_name')['final_rating'].mean().sort_values(ascending=False)
                st.bar_chart(strategy_effectiveness)
                st.caption("Average jailbreak rating (0-10) per strategy.")

        with viz_col2:
            st.subheader("Vulnerability per Task")
            if 'task_id' in df_viz.columns and not df_viz['task_id'].empty:
                task_vulnerability = df_viz.groupby('task_id')['final_rating'].mean().sort_values(ascending=False)
                st.bar_chart(task_vulnerability)
                st.caption("Average jailbreak rating (0-10) per task.")

        st.subheader("Heatmap: Strategy vs. Task Success")
        if 'strategy_name' in df_viz.columns and 'task_id' in df_viz.columns:
            # Ensure there's enough diversity for a pivot table
            if df_viz['strategy_name'].nunique() > 0 and df_viz['task_id'].nunique() > 0:
                try:
                    heatmap_data = df_viz.pivot_table(
                        index='strategy_name', 
                        columns='task_id', 
                        values='final_rating',
                        aggfunc='mean'  # Use mean for aggregation
                    ).fillna(0)

                    if not heatmap_data.empty:
                        st.dataframe(
                            heatmap_data.style.background_gradient(cmap='viridis', axis=None).format("{:.1f}"),
                            use_container_width=True
                        )
                    else:
                         st.info("Not enough data to create a heatmap yet.")
                except Exception as e:
                    st.error(f"Could not generate heatmap: {e}")
            else:
                st.info("Not enough data for a heatmap (need at least one task and one strategy with results).")