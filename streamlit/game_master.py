import streamlit as st
from string import Template
import pymongo
from pymongo.server_api import ServerApi

from beer_game.game_repo import GameRepo
from beer_game.mongodb_adapter import MongoDB


CHECKED_ICON = ":green[:material/check_box:]"
UNCHECKED_ICON = ":red[:material/check_box_outline_blank:]"

PURCHASED_ICON = ":green[:material/lock:]"
NOTPURCHASED_ICON = ":red[:material/money_bag:]"

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Beer Game (Game Master)",
    page_icon="🍺",
)


# =========================
# MongoDB Connection
# =========================
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(
        st.secrets["mongo"]["uri"],
        server_api=ServerApi("1")
    )


# =========================
# Sidebar (Game Master)
# =========================
with st.sidebar:
    st.title("Game Master")

    admin_key = st.text_input(
        "admin_key",
        type="password",
        key="admin_key",
        disabled=("game" in st.session_state)
    )

    game_id = st.text_input(
        "game_id",
        key="game_id",
        disabled=("game" in st.session_state)
    )

    enabled = (
        admin_key == st.secrets["admin"]["key"]
    )

    if st.button(
        "New Game",
        disabled=(not enabled or not game_id or "game" in st.session_state)
    ):
        client = init_connection()
        db = MongoDB(client)
        st.session_state.game = GameRepo(game_id, db)
        st.session_state.game.newGame()
        st.success(f"{game_id} started")

    if st.button(
        "End Game",
        disabled=("game" not in st.session_state)
    ):
        st.session_state.game.endGame()
        del st.session_state["game"]
        st.success("Game ended")


# =========================
# Main Dashboard
# =========================
if "game" in st.session_state:

    gameRepo: GameRepo = st.session_state.game
    dashboard = gameRepo.getDashboard()
    week = dashboard["week"]

    st.title(f"Week {week}")

    st.markdown("""
### Game Flow
1. Refresh
2. Adjust order number
3. Place Order
4. Wait shop player
5. Wait retailer player
6. Wait factory player
7. Next Week

⬇️ Start here
""")

    # -------- Controls --------
    left, mid1, mid2, right = st.columns(4)

    left.button("Refresh")

    order = mid1.number_input(
        "Order",
        step=1,
        value=None,
        placeholder="Order",
        label_visibility="collapsed"
    )

    if mid2.button("Place Order", disabled=(order is None)):
        gameRepo.dispatch(order)
        st.success(f"Order {order} dispatched")

    if right.button("Next Week"):
        gameRepo.nextWeek()
        st.success("Moved to next week")

    # -------- Player Status --------
    players = gameRepo.reloadPlayerStat()
    n_players = len(players)

    st.text(f"{n_players} players")

    tabs = st.tabs(list(players.keys()) or ["No Player"])

    for idx, (player, roles) in enumerate(players.items()):
        with tabs[idx]:

            PLAYER_STAT = Template("""
- **$player**
    - Shop: $shop $shop_purchased
    - Retailer: $retailer $retailer_purchased
    - Factory: $factory $factory_purchased
    - **Total Cost:** $total_cost
""")

            st.markdown(
                PLAYER_STAT.substitute(
                    player=player,
                    shop=CHECKED_ICON
                    if roles["shop"]["enabled"] else UNCHECKED_ICON,
                    retailer=CHECKED_ICON
                    if roles["retailer"]["enabled"] else UNCHECKED_ICON,
                    factory=CHECKED_ICON
                    if roles["factory"]["enabled"] else UNCHECKED_ICON,
                    shop_purchased=PURCHASED_ICON
                    if roles["shop"]["purchased"] else NOTPURCHASED_ICON,
                    retailer_purchased=PURCHASED_ICON
                    if roles["retailer"]["purchased"] else NOTPURCHASED_ICON,
                    factory_purchased=PURCHASED_ICON
                    if roles["factory"]["purchased"] else NOTPURCHASED_ICON,
                    total_cost=sum(
                        roles[r]["cost"] for r in roles
                    )
                )
            )

            # デバッグ用（不要なら削除）
            st.write(roles)
