import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Chess Stats Dashboard", page_icon="♟️")

st.title("♟️ Chess Stats Dashboard")
st.write("Analyze your Chess.com games!")

username = st.text_input("Please enter your Chess.com username:")

#bypass cloudflare protection
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

if username:
    st.write(f"Retrieving data for {username}...")

    archive_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    response = requests.get(archive_url, headers=headers)

    if response.status_code != 200:
        st.error(f"❌ Error {response.status_code}: Failed to fetch archives for {username}.")
        st.stop()

    try:
        data = response.json()
    except ValueError:
        st.error("⚠️ Failed to parse JSON. Showing raw response:")
        st.code(response.text[:300])
        st.stop()

    if "archives" not in data or not data["archives"]:
        st.error("No archives found — account may be private or inactive.")
        st.stop()


    archives = data["archives"]
    month_options = [url.split("/")[-2] + "/" + url.split("/")[-1] for url in archives]
    selected_month = st.selectbox("Select a month to view:", month_options, index=len(month_options)-1)
    selected_url = [url for url in archives if selected_month in url][0]

    games_response = requests.get(selected_url, headers=headers)

    if games_response.status_code != 200:
        st.error(f"❌ Error {games_response.status_code}: Could not fetch games.")
        st.stop()

    try:
        games_data = games_response.json()
    except ValueError:
        st.error("⚠️ Could not parse games JSON.")
        st.stop()

    games = games_data.get("games", [])

    if not games:
        st.warning("No games found for this month 😢")
        st.stop()

    df = pd.json_normalize(games)
    st.success(f"Loaded {len(df)} games!")

    results = []
    for g in games:
        if g["white"]["username"].lower() == username.lower():
            color = "white"
        else:
            color = "black"
        results.append(g[color]["result"])

    result_df = pd.Series(results).value_counts().reset_index()
    result_df.columns = ["result", "count"]

    st.subheader("Results in Most Recent Month")
    fig = px.bar(result_df, x="result", y="count", title="Game Results", text="count")
    st.plotly_chart(fig)
