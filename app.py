import streamlit as st
import pandas as pd
import glob
import os
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# Basic page setup
st.set_page_config(page_title="Diamond Standard Ratings", layout="wide")

# --- 1. DATA LOADING FUNCTIONS ---
def get_rpi_data():
    # Looks for game files in the root folder of your GitHub repo
    file_pattern = 'College Baseball Games/cbase_games_*.csv'
    game_files = glob.glob(file_pattern)

    if not game_files:
        return None

    records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'opponents': []})

    for file in game_files:
        df = pd.read_csv(file)
        for _, row in df.iterrows():
            away = str(row['Away Team']).strip()
            home = str(row['Home Team']).strip()
            score_str = str(row['Final Score']).strip()

            winner = away if score_str.startswith(away) else (home if score_str.startswith(home) else None)
            if not winner: continue

            records[away]['opponents'].append(home)
            records[home]['opponents'].append(away)

            if winner == away:
                records[away]['wins'] += 1
                records[home]['losses'] += 1
            else:
                records[home]['wins'] += 1
                records[away]['losses'] += 1

    # RPI Math (40/40/20)
    wp = {t: d['wins']/(d['wins']+d['losses']) for t, d in records.items() if (d['wins']+d['losses']) > 0}
    owp = {t: sum(wp[o] for o in d['opponents'] if o in wp)/len(d['opponents']) for t, d in records.items() if d['opponents']}
    oowp = {t: sum(owp[o] for o in d['opponents'] if o in owp)/len(d['opponents']) for t, d in records.items() if d['opponents']}

    final_results = []
    for team in records:
        score = (wp.get(team, 0) * 0.4) + (owp.get(team, 0) * 0.4) + (oowp.get(team, 0) * 0.2)
        final_results.append({
            'Team': team,
            'Record': f"{records[team]['wins']}-{records[team]['losses']}",
            'RPI': round(score, 5),
            'WP': round(wp.get(team, 0), 4),
            'OWP': round(owp.get(team, 0), 4),
            'OOWP': round(oowp.get(team, 0), 4)
        })
    # Step 6: Create and Sort DataFrame
    rpi_df = pd.DataFrame(final_results).sort_values(by='RPI', ascending=False).reset_index(drop=True)

    # --- THE ADDITION: Add a Rank Column ---
    # This creates a list from 1 to the total number of teams
    rpi_df.insert(0, 'Rank', range(1, len(rpi_df) + 1))
    
    # Optional: Add a '#' to the rank for style
    rpi_df['Rank'] = '#' + rpi_df['Rank'].astype(str)

    return rpi_df
    return pd.DataFrame(final_results).sort_values(by='RPI', ascending=False).reset_index(drop=True)

def get_efficiency_data():
    file_path = 'baseball_stats.csv'
    if not os.path.exists(file_path): 
        return None
    
    df_raw = pd.read_csv(file_path)
    try:
        # Helper list to process each conference block
        # Format: (Column Name, OPS Column, RA/G Column, Conference Label)
        conf_blocks = [
            ('SEC', 'ops', 'ra/g', 'SEC'),
            ('ACC', 'ops.1', 'ra/g.1', 'ACC'),
            ('Big 10', 'ops.2', 'ra/g.2', 'Big 10'),
            ('Big 12', 'ops.3', 'ra/g.3', 'Big 12'),
            ('Mid-Major', 'ops.4', 'ra/g.4', 'Mid-Major')
        ]
        
        all_confs = []
        
        for team_col, ops_col, ra_col, label in conf_blocks:
            if team_col in df_raw.columns:
                temp_df = df_raw[[team_col, ops_col, ra_col]].copy().dropna(subset=[team_col])
                temp_df.columns = ['Team', 'OPS', 'RA_per_G']
                temp_df['Conference'] = label
                all_confs.append(temp_df)
        
        combined = pd.concat(all_confs, ignore_index=True)

        # Force numeric conversion to prevent the TypeError you saw earlier
        combined['OPS'] = pd.to_numeric(combined['OPS'], errors='coerce')
        combined['RA_per_G'] = pd.to_numeric(combined['RA_per_G'], errors='coerce')

        return combined.dropna(subset=['OPS', 'RA_per_G'])
        
    except Exception as e:
        st.error(f"Error processing stats: {e}")
        return None

# --- 2. SIDEBAR (Only defined ONCE to avoid Duplicate ID error) ---
st.sidebar.title("💎 Diamond Standard")
page = st.sidebar.radio("Navigate", ["Home", "RPI Leaderboard", "Efficiency Analysis"])

# --- 3. PAGE LOGIC ---
if page == "Home":
    st.title("⚾ Welcome to Diamond Standard Ratings")
    st.write("Custom analytics for D1 Baseball.")
    st.info("Download your CSV from Drive and upload to GitHub to update these charts.")

elif page == "RPI Leaderboard":
    st.title("🏆 Live RPI Rankings")
    rpi_df = get_rpi_data()
    if rpi_df is not None:
        st.dataframe(rpi_df, use_container_width=True, hide_index=True)
    else:
        st.error("No game files found. Ensure 'cbase_games_*.csv' is in your GitHub repo.")

elif page == "Efficiency Analysis":
    st.title("📊 Efficiency: OPS vs. Runs Allowed")
    eff_df = get_efficiency_data()
    
    if eff_df is not None:
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.set_style("whitegrid")
        
        # Quadrant lines (Averages)
        avg_ops = eff_df['OPS'].mean()
        avg_ra = eff_df['RA_per_G'].mean()
        ax.axvline(avg_ops, color='black', linestyle='--', alpha=0.3)
        ax.axhline(avg_ra, color='black', linestyle='--', alpha=0.3)
      

        # Plot teams
        for _, row in eff_df.iterrows():
            color = 'red' if row['Conference'] == 'SEC' else 'blue'
            ax.scatter(row['OPS'], row['RA_per_G'], color=color, s=100, edgecolors='black', alpha=0.6)
            ax.text(row['OPS'], row['RA_per_G'], row['Team'], fontsize=8, ha='center', va='bottom')


        plt.gca().invert_yaxis() # Lower RA/G is better
        ax.set_xlabel("Offensive OPS")
        ax.set_ylabel("Runs Allowed Per Game")
        st.pyplot(fig)    
    else:
        st.error("Stats file 'baseball_stats.csv' not found.")

   
        with st.expander("📖 How to read this Efficiency Analysis", expanded=True):
            st.markdown("""
            ### **Core Metrics**
            * **Offensive OPS (X-Axis):** Measures a team's ability to get on base and hit for power. High values indicate a dangerous offense.
            * **Runs Allowed Per Game (Y-Axis):** Measures pitching and defensive efficiency. **Note:** This axis is inverted, so elite defenses appear at the top.
            
            ---
            ### **The Four Quadrants**
            * **Upper Right (Elite):** Above-average offense paired with above-average defense.
            * **Upper Left:** High-tier defense struggling to find offensive production.
            * **Lower Right:** High-octane offense being held back by pitching/defense.
            * **Lower Left:** Below-average performance in both categories.
            
            ---
            ### **It would be too much to put all 307 D1 College Baseball teams onto one graph. Therefore, I decided to do the ACC, SEC, Big 10, Big 12, and 26 mid-majors that are having good seasons this year, and that typically have good seasons.**
            Write your specific takeaways for this week here. For example: *"Many of the teams that appear elite by these graphs have not faced real competition yet."*
            """)
