import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="College Baseball Analytics", layout="wide")
st.title("⚾ College Baseball Analytics")

# Load your uploaded CSV
try:
    df = pd.read_csv('data/game_logs.csv')
    
    # --- RPI CALCULATION ---
    # This assumes your CSV has columns: 'WP', 'OWP', and 'OOWP'
    df['Custom_RPI'] = (df['WP'] * 0.4) + (df['OWP'] * 0.4) + (df['OOWP'] * 0.2)
    
    # --- EFFICIENCY CHART ---
    st.subheader("Offensive OPS vs. Runs Allowed")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plotting teams as simple dots
    ax.scatter(df['OPS'], df['Runs_Allowed'], alpha=0.7, c='blue', edgecolors='black')

    # Label teams
    for i, txt in enumerate(df['Team']):
        ax.annotate(txt, (df['OPS'].iat[i], df['Runs_Allowed'].iat[i]), size=8, alpha=0.7)

    ax.set_xlabel("Offensive OPS (Higher is Better)")
    ax.set_ylabel("Runs Allowed Per Game (Lower is Better)")
    plt.gca().invert_yaxis() # Better defense is at the top
    ax.grid(True, linestyle='--', alpha=0.5)
    
    st.pyplot(fig)

    # --- RPI RANKINGS TABLE ---
    st.subheader("Live RPI Rankings")
    st.dataframe(df[['Team', 'Custom_RPI']].sort_values(by='Custom_RPI', ascending=False))

except Exception as e:
    st.error(f"Waiting for data... Make sure 'data/game_logs.csv' is uploaded. Error: {e}")
