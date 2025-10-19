import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.title("♟️ Chess Stats Dashboard")
st.text("Analyze your chess.com games!")

username = st.text_input("Please enter your chess.com username!")

if(username):
    st.write(f'Retrieving data for {username}...')

    archive_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    archives = requests.get(archive_url).json()["archives"]

    latest = archives[-1]
    games = requests.get(latest).json()["games"]

    if not games:
        st.error("No games found for this month.. elo -67")
    else:
        df = pd.json_normalize(games)
        st.write(f"Loaded {len(df)} games")

        results = []
        for g in games:
            if g["white"]["username"].lower() == username.lower():
                color = white
            else:
                color = black

            results.append(g[color]["result"])

        result_df = pd.Series(results).value_counts()
        st.subheader("Results in Most Recent Month")
        st.bar_chart(result_df)