import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import random
import os

# Chemin du fichier CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "lineups_rentabilite.csv")
data = pd.read_csv(file_path)

# Définir les statistiques
offensive_stats = ["Rentabilite_possessions_equipe", "Rentabilite_temps_equipe", "True_Shooting_equipe_%"]
defensive_stats = ["Rentabilite_possessions_opp", "Rentabilite_temps_opp", "True_Shooting_opp_%"]
all_stats = offensive_stats + defensive_stats

# Dictionnaire pour renommer les statistiques
stat_rename = {
    "Rentabilite_possessions_equipe": "Points par poss. (offense)",
    "Rentabilite_temps_equipe": "Poss par match (offense)",
    "True_Shooting_equipe_%": "TS% (offense)",
    "Rentabilite_possessions_opp": "Points par poss. (defense)",
    "Rentabilite_temps_opp": "Poss par match (defense)",
    "True_Shooting_opp_%": "TS% (defense)"
}

# Fonction pour calculer les comparaisons de matchups
def calculate_matchup(team_lineups, opponent_lineups):
    results = []
    for _, lineup in team_lineups.iterrows():
        lineup_id = f"{lineup['Lineup']} ({lineup['Plus/Minus']})"  # Identifiant combiné
        row = {"Lineup": lineup_id}

        for stat in all_stats:
            if stat in offensive_stats:
                opp_stat = stat.replace("equipe", "opp")
                opponent_stat_mean = opponent_lineups[opp_stat].mean()
                row[stat] = lineup[stat] - opponent_stat_mean
            else:
                opp_stat = stat.replace("opp", "equipe")
                opponent_stat_mean = opponent_lineups[opp_stat].mean()
                row[stat] = lineup[stat] - opponent_stat_mean

        results.append(row)
    return pd.DataFrame(results)

# Fonction pour afficher la heatmap
def plot_heatmap(df, title):
    fig, ax = plt.subplots()
    df = df.rename(columns=stat_rename).set_index("Lineup").select_dtypes(include='number')
    sns.heatmap(df, annot=True, fmt=".1f", cmap="coolwarm", linewidths=0.5, ax=ax)

    # Ajouter une ligne épaisse pour séparer les statistiques offensives et défensives
    ax.hlines(y=len(offensive_stats), xmin=0, xmax=df.shape[1], linewidth=3, color='black')

    ax.set_title(title)
    st.pyplot(fig)

# Fonction pour le radar chart
def radar_chart(team1_lineups, team2_lineups):
    categories = ["Points par poss. (offense)", "Points par poss. (defense)",
                  "Poss par match (offense)", "Poss par match (defense)",
                  "TS% (offense)", "TS% (defense)"]

    fig = go.Figure()
    unique_lineups = list(set(team1_lineups + team2_lineups))
    color_mapping = {lineup: f"#{random.randint(0, 0xFFFFFF):06x}" for lineup in unique_lineups}

    # Ajouter les lineups des deux équipes
    for lineup in team1_lineups + team2_lineups:
        row = data[data["Lineup"] == lineup].iloc[0]
        values = [row[stat] for stat in all_stats]
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name=lineup,
            line=dict(color=color_mapping[lineup])
        ))

    fig.update_layout(title="Graphique Radar", polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    st.plotly_chart(fig)

# Interface Streamlit
st.title("Analyse de Rentabilité des Lineups 🏀📊")
st.sidebar.header("Filtres")

# Sélection des équipes
team_name = st.sidebar.selectbox("Équipe de référence", data["Equipe"].unique())
opponent_name = st.sidebar.selectbox("Équipe adverse", [team for team in data["Equipe"].unique() if team != team_name])

# Sélection des joueurs
player_filter_team = st.sidebar.multiselect("Joueurs de l'équipe de référence", data.columns[2:7].unique())
player_filter_opponent = st.sidebar.multiselect("Joueurs de l'équipe adverse", data.columns[2:7].unique())

# Filtrage des données
team_data = data[data["Equipe"] == team_name]
if player_filter_team:
    team_data = team_data.query("Player_1_name in @player_filter_team or Player_2_name in @player_filter_team or \
                                 Player_3_name in @player_filter_team or Player_4_name in @player_filter_team or \
                                 Player_5_name in @player_filter_team")

opponent_data = data[data["Equipe"] == opponent_name]
if player_filter_opponent:
    opponent_data = opponent_data.query("Player_1_name in @player_filter_opponent or Player_2_name in @player_filter_opponent or \
                                         Player_3_name in @player_filter_opponent or Player_4_name in @player_filter_opponent or \
                                         Player_5_name in @player_filter_opponent")

# Affichage Heatmap
st.subheader(f"Heatmap : {team_name} vs {opponent_name}")
matchup_df = calculate_matchup(team_data, opponent_data)
plot_heatmap(matchup_df, f"Heatmap pour {team_name} contre {opponent_name}")

# Affichage Radar Chart
st.subheader("Radar Chart")
team1_lineups = st.multiselect(f"Lineups de {team_name} :", options=team_data["Lineup"].unique())
team2_lineups = st.multiselect(f"Lineups de {opponent_name} :", options=opponent_data["Lineup"].unique())
radar_chart(team1_lineups, team2_lineups)
