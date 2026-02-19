import streamlit as st

pg = st.navigation(
    [
        "streamlit/home.py",
        "streamlit/player.py",
        "streamlit/game_master.py",
    ]
)
pg.run()
