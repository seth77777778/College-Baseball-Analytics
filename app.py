import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import glob
from collections import defaultdict

# --- REMOVED GOOGLE DRIVE IMPORTS ---
st.set_page_config(page_title="Diamond Standard Ratings", layout="wide")

# --- DATA LOADING FUNCTIONS ---
def get_rpi_data():
    # UPDATED: Look for files in the same folder as app.py on GitHub
    file_pattern = 'cbase_games_*.csv' 
    game_files = glob.glob(file_pattern)
    
    if not game_files: 
        return None

    records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'opponents': []})
    for file in game_files:
        df_game = pd.read_csv(file)
        for _, row in df_game.iterrows():
            away, home = str(row['Away Team']).strip(), str(row['Home Team']).strip()
            score_str = str(row['Final Score']).strip()
            # Logic to determine winner
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

    # Calculation math
    wp = {t: d['wins']/(d['wins']+d['losses']) for t, d in records.items() if (d['wins']+d['losses']) > 0}
    owp = {t: sum(wp[o] for o in d['opponents'] if o in wp)/len(d['opponents']) for t, d in records.items() if d['opponents']}
    oowp = {t: sum(owp[o] for o in d['opponents'] if o in owp)/len(d['opponents']) for t, d in records.items() if d['opponents']}

    results = []
    for team in records:
        score = (wp.get(team, 0) * 0.4) + (owp.get(team, 0) * 0.4) + (oowp.get(team, 0) * 0.2)
        results.append({'Team': team, 'Record': f"{records[team]['wins']}-{records[team]['losses']}", 'RPI': round(score, 5)})
    
    return pd.DataFrame(results).sort_values(by='RPI', ascending=False)

def get_efficiency_data():
    # UPDATED: Changed to look for the CSV file you uploaded to GitHub
    file_path = 'baseball_stats.csv' 
    if not os.path.exists(file_path): 
        return None
        
    df_raw = pd.read_csv(file_path) # Changed from read_excel to read_csv
    try:
        # SEC Teams
        df_sec = df_raw[['SEC', 'ops', 'ra/g']].copy().dropna(subset=['SEC'])
        df_sec.columns = ['Team', 'OPS', 'RA_per_G']
        df_sec['Conference'] = 'SEC'
        
        # ACC Teams
        df_acc = df_raw[['ACC', 'ops.1', 'ra/g.1']].copy().dropna(subset=['ACC'])
        df_acc.columns = ['Team', 'OPS', 'RA_per_G']
        df_acc['Conference'] = 'ACC'
        
        combined = pd.concat([df_sec, df_acc], ignore_index=True)
        combined['OPS'] = pd.to_numeric(combined['OPS'], errors='coerce')
        combined['RA_per_G'] = pd.to_numeric(combined['RA_per_G'], errors='coerce')
        return combined.dropna(subset=['OPS', 'RA_per_G'])
    except: 
        return None

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("💎 Diamond Standard")
page = st.sidebar.radio("Navigate", ["Home", "RPI Leaderboard", "Efficiency Analysis"])

# --- PAGE CONTENT ---
if page == "Home":
    st.title("⚾ Welcome to Diamond Standard Ratings")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("🔄 Update Schedule")
        st.info("**RPI Rankings:** Updated Daily")
        st.info("**Efficiency Graphs:** Updated Weekly")
    
    with col2:
        st.header("📊 About the Model")
        st.write("""
        Custom analytics for D1 Baseball.
        - **RPI:** 40/40/20 weighted formula.
        - **Efficiency:** OPS vs. Runs Allowed per Game.
        """)

elif page == "RPI Leaderboard":
    st.title("⚾ Live RPI Leaderboard")
    rpi_df = get_rpi_data()
    if rpi_df is not None:
        st.dataframe(rpi_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No game data found. Make sure cbase_games_*.csv files are uploaded.")

elif page == "Efficiency Analysis":
    st.title("📈 Efficiency: OPS vs. Runs Allowed")
    eff_df = get_efficiency_data()
    
    if eff_df is not None:
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.set_style("whitegrid")
        
        # Quadrant averages
        avg_ops = eff_df['OPS'].mean()
        avg_ra = eff_df['RA_per_G'].mean()
        ax.axvline(avg_ops, color='black', linestyle='--', alpha=0.3)
        ax.axhline(avg_ra, color='black', linestyle='--', alpha=0.3)

        for _, row in eff_df.iterrows():
            color = 'red' if row['Conference'] == 'SEC' else 'blue'
            ax.scatter(row['OPS'], row['RA_per_G'], color=color, s=100, edgecolors='black', alpha=0.6)
            ax.text(row['OPS'], row['RA_per_G'], row['Team'], fontsize=8, ha='center', va='bottom')

        # Annotations
        max_ops, min_ops = eff_df['OPS'].max(), eff_df['OPS'].min()
        max_ra, min_ra = eff_df['RA_per_G'].max(), eff_df['RA_per_G'].min()
        
        ax.text(max_ops, min_ra, "Elite", color='green', fontweight='bold')
        ax.text(min_ops, max_ra, "Underperforming", color='red', fontweight='bold')

        plt.gca().invert_yaxis()
        ax.set_xlabel("Offensive OPS")
        ax.set_ylabel("Runs Allowed Per Game")
        st.pyplot(fig)
    else:
        st.warning("Stats file not found. Please upload 'baseball_stats.csv'.")
 elif page == "Efficiency Analysis":
    st.title("📈 Efficiency: OPS vs. Runs Allowed")
    eff_df = get_efficiency_data()
    
    if eff_df is not None:
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.set_style("whitegrid")
        
        # Quadrant averages
        avg_ops = eff_df['OPS'].mean()
        avg_ra = eff_df['RA_per_G'].mean()
        ax.axvline(avg_ops, color='black', linestyle='--', alpha=0.3)
        ax.axhline(avg_ra, color='black', linestyle='--', alpha=0.3)

        for _, row in eff_df.iterrows():
            color = 'red' if row['Conference'] == 'SEC' else 'blue'
            ax.scatter(row['OPS'], row['RA_per_G'], color=color, s=100, edgecolors='black', alpha=0.6)
            ax.text(row['OPS'], row['RA_per_G'], row['Team'], fontsize=8, ha='center', va='bottom')

        # Annotations
        max_ops, min_ops = eff_df['OPS'].max(), eff_df['OPS'].min()
        max_ra, min_ra = eff_df['RA_per_G'].max(), eff_df['RA_per_G'].min()
        
        ax.text(max_ops, min_ra, "Elite", color='green', fontweight='bold')
        ax.text(min_ops, max_ra, "Underperforming", color='red', fontweight='bold')

        plt.gca().invert_yaxis()
        ax.set_xlabel("Offensive OPS")
        ax.set_ylabel("Runs Allowed Per Game")
        st.pyplot(fig)
    else:
        st.warning("Stats file not found. Please upload 'baseball_stats.csv'.")






import streamlit as st
import pandas as pd
import glob
import os
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Diamond Standard Ratings", layout="wide")

# --- DATA LOADING & RPI CALCULATION ---
def get_rpi_data():
    # Looks for any file starting with cbase_games_ in your GitHub repo
    file_pattern = 'cbase_games_*.csv'
    game_files = glob.glob(file_pattern)

    if not game_files:
        return None

    records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'opponents': []})

    # Your logic: Accumulate game results
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

    # Math Steps
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
    
    return pd.DataFrame(final_results).sort_values(by='RPI', ascending=False).reset_index(drop=True)

def get_efficiency_data():
    # Looks for the stats file you uploaded
    file_path = 'baseball_stats.csv'
    if not os.path.exists(file_path): return None
    
    df_raw = pd.read_csv(file_path)
    try:
        # Combining SEC and ACC logic from your previous snippet
        df_sec = df_raw[['SEC', 'ops', 'ra/g']].copy().dropna(subset=['SEC'])
        df_sec.columns = ['Team', 'OPS', 'RA_per_G']
        df_sec['Conference'] = 'SEC'
        
        df_acc = df_raw[['ACC', 'ops.1', 'ra/g.1']].copy().dropna(subset=['ACC'])
        df_acc.columns = ['Team', 'OPS', 'RA_per_G']
        df_acc['Conference'] = 'ACC'
        
        combined = pd.concat([df_sec, df_acc], ignore_index=True)
        return combined
    except: return None

# --- SIDEBAR ---
st.sidebar.title("💎 Diamond Standard")
page = st.sidebar.radio("Navigate", ["Home", "RPI Leaderboard", "Efficiency Analysis"])

# --- PAGES ---
if page == "Home":
    st.title("⚾ Diamond Standard Ratings")
    st.write("Welcome to your custom college baseball analytics hub.")
    st.info("Upload new CSVs to GitHub to update the data below.")

elif page == "RPI Leaderboard":
    st.title("🏆 Live RPI Rankings")
    rpi_df = get_rpi_data()
    if rpi_df is not None:
        st.dataframe(rpi_df, use_container_width=True, hide_index=True)
    else:
        st.error("No game files found. Please upload files named 'cbase_games_...csv' to GitHub.")

elif page == "Efficiency Analysis":
    st.title("📊 Team Efficiency Plot")
    eff_df = get_efficiency_data()
    if eff_df is not None:
        fig, ax = plt.subplots(figsize=(10, 6))
        # Simple scatter plot using your columns
        sns.scatterplot(data=eff_df, x='OPS', y='RA_per_G', hue='Conference', s=100)
        
        # Invert Y because lower Runs Allowed is better
        plt.gca().invert_yaxis()
        
        # Adding labels for teams
        for i, txt in enumerate(eff_df['Team']):
            ax.annotate(txt, (eff_df['OPS'].iat[i], eff_df['RA_per_G'].iat[i]), size=7)
            
        st.pyplot(fig)
    else:
        st.error("Stats file 'baseball_stats.csv' not found.")
