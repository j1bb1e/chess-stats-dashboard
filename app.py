import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit.components.v1 import html

st.set_page_config(page_title="Chess Stats Dashboard", page_icon="♟️", layout="wide")

html("""
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
<style>
header, footer {visibility: hidden;}
.stApp {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Montserrat', sans-serif;
}
div.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 1100px;
    margin: auto;
}
input, textarea, select {
    background-color: #1e1e1e !important;
    color: #fafafa !important;
    border: 1px solid #333 !important;
    border-radius: 6px !important;
    font-family: 'Montserrat', sans-serif !important;
}
[data-testid="stMetricValue"] {
    font-size: 32px;
    color: #81c784;
    font-family: 'Montserrat', sans-serif !important;
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
    color: #ccc;
    font-family: 'Montserrat', sans-serif !important;
}
[data-testid="stDataFrame"] {
    font-family: 'Montserrat', sans-serif !important;
}
h1, h2, h3, h4, h5, h6, p, span, label, div {
    font-family: 'Montserrat', sans-serif !important;
}
hr {border: 1px solid #333;}
</style>
""")

st.title("♟️ Chess Stats Dashboard")
st.caption("Analyze your Chess.com performance!")

username = st.text_input("Enter your Chess.com username:")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://www.chess.com/",
    "Origin": "https://www.chess.com",
}

if username:
    with st.spinner("Fetching player data..."):
        archive_url = f"https://api.chess.com/pub/player/{username}/games/archives"
        response = requests.get(archive_url, headers=headers)

    if response.status_code != 200:
        st.error(f"❌ Error {response.status_code}: Could not fetch archives for {username}.")
        st.stop()

    data = response.json()
    archives = data.get("archives", [])
    if not archives:
        st.error("No archives found — account may be private or inactive.")
        st.stop()

    profile, current_rating = {}, None
    try:
        profile_resp = requests.get(f"https://api.chess.com/pub/player/{username}", headers=headers)
        if profile_resp.status_code == 200 and profile_resp.text.strip():
            profile = profile_resp.json()
        stats = requests.get(f"https://api.chess.com/pub/player/{username}/stats", headers=headers).json()
        for mode in ["chess_rapid", "chess_blitz", "chess_bullet"]:
            if mode in stats and "last" in stats[mode]:
                current_rating = stats[mode]["last"]["rating"]
                break
    except Exception:
        pass

    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 3])
    with col1:
        avatar_url = profile.get(
            "avatar",
            "https://www.chess.com/bundles/web/images/noavatar_l.84a92436.gif"
        )
        st.image(avatar_url, width=120)
    with col2:
        st.markdown(f"### {profile.get('username', username)}")
        if 'country' in profile:
            country_code = profile['country'].split('/')[-1].upper()
            st.markdown(f"**🌍 Country:** {country_code}")
        if current_rating:
            st.markdown(f"**🏅 Current Elo:** {current_rating}")
        st.markdown(f"**👤 Status:** {profile.get('status', 'N/A').capitalize()}")
    st.markdown("<hr>", unsafe_allow_html=True)

    month_options = [url.split("/")[-2] + "/" + url.split("/")[-1] for url in archives]
    selected_month = st.selectbox("Select a month:", month_options, index=len(month_options) - 1)
    selected_url = next(url for url in archives if selected_month in url)

    with st.spinner(f"Loading games for {selected_month}..."):
        games_response = requests.get(selected_url, headers=headers)

    if games_response.status_code != 200:
        st.error(f"❌ Error {games_response.status_code}: Failed to fetch games.")
        st.stop()

    games_data = games_response.json()
    games = games_data.get("games", [])
    if not games:
        st.warning("No games found for this month 😢")
        st.stop()

    df = pd.json_normalize(games)
    st.success(f"✅ Loaded {len(df)} games for {selected_month}")

    results = []
    for g in games:
        color = "white" if g["white"]["username"].lower() == username.lower() else "black"
        result = g[color]["result"].lower()
        if result == "win":
            results.append("Win")
        elif result in ["checkmated", "timeout", "resigned", "lose"]:
            results.append("Loss")

    result_df = pd.Series(results).value_counts().reset_index()
    result_df.columns = ["Result", "Count"]
    result_df = result_df[result_df["Result"].isin(["Win", "Loss"])]
    total_games = result_df["Count"].sum()
    result_df["Percent"] = (result_df["Count"] / total_games * 100).round(1)
    win_rate = (
        result_df.loc[result_df["Result"] == "Win", "Percent"].values[0]
        if "Win" in result_df["Result"].values
        else 0
    )

    overview_tab, rating_tab = st.tabs(["📊 Overview", "📈 Rating Progression"])

    with overview_tab:
        st.markdown("## 🎯 Game Results Overview")
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.metric("Total Games", total_games)
        with col2:
            st.metric("Win Rate", f"{win_rate}%")
        with col3:
            st.metric("Current Elo", current_rating if current_rating else "N/A")

        st.dataframe(
            result_df.style
            .format({"Percent": "{:.1f}%"})
            .set_properties(
                **{
                    "text-align": "center",
                    "color": "#ffffff",
                    "background-color": "#1e1e1e",
                    "border": "1px solid #333",
                    "font-size": "16px",
                    "font-family": "'Montserrat', sans-serif",
                }
            )
            .hide(axis="index"),
            use_container_width=True,
        )

        fig = px.bar(
            result_df.sort_values("Result", ascending=False),
            x="Result",
            y="Count",
            text="Percent",
            color="Result",
            color_discrete_map={"Win": "#4CAF50", "Loss": "#E53935"},
            title=f"Results for {selected_month}",
        )
        fig.update_traces(
            texttemplate="%{text}%",
            textposition="outside",
            textfont=dict(size=14, color="#ffffff", family="Montserrat"),
        )
        fig.update_layout(
            transition_duration=500,
            title=dict(x=0.5, font=dict(size=22, color="#fafafa", family="Montserrat")),
            xaxis=dict(title="", tickfont=dict(size=14, color="#e0e0e0", family="Montserrat")),
            yaxis=dict(title="Games", tickfont=dict(color="#e0e0e0", family="Montserrat"), gridcolor="#333"),
            plot_bgcolor="#1e1e1e",
            paper_bgcolor="#121212",
            showlegend=False,
            margin=dict(t=60, b=40, l=60, r=20),
            font=dict(family="Montserrat", color="#ffffff"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with rating_tab:
        st.markdown("## 📈 Rating Progression Over Time")
        st.divider()
        ratings = []
        for archive in archives[-12:]:
            try:
                games_data = requests.get(archive, headers=headers).json()
                for g in reversed(games_data.get("games", [])):
                    if g["white"]["username"].lower() == username.lower():
                        player = g["white"]
                    elif g["black"]["username"].lower() == username.lower():
                        player = g["black"]
                    else:
                        continue
                    if "rating" in player:
                        month = archive.split("/")[-2] + "/" + archive.split("/")[-1]
                        ratings.append({"Month": month, "Rating": player["rating"]})
                        break
            except Exception:
                continue
        if ratings:
            ratings_df = pd.DataFrame(ratings).sort_values("Month")
            line_fig = px.line(
                ratings_df,
                x="Month",
                y="Rating",
                markers=True,
                title=f"{username}'s Rating Over Time",
            )
            line_fig.update_traces(
                line=dict(color="#4CAF50", width=3),
                marker=dict(size=8, color="#81c784"),
            )
            line_fig.update_layout(
                yaxis_title="Rating",
                xaxis_title="Month",
                plot_bgcolor="#1e1e1e",
                paper_bgcolor="#121212",
                font=dict(family="Montserrat", color="#e0e0e0"),
                title=dict(x=0.5, font=dict(size=22, color="#fafafa", family="Montserrat")),
                margin=dict(t=60, b=40, l=60, r=20),
            )
            st.plotly_chart(line_fig, use_container_width=True)
        else:
            st.info("No rating data available to display.")

    st.markdown(
        """
        <hr>
        <center>
        <p style='font-size:15px; color:#aaa; font-family:Montserrat, sans-serif;'>
        Built by <b>Julia Brand</b> using Python, Streamlit & Plotly :)
        </p>
        </center>
        """,
        unsafe_allow_html=True,
    )
