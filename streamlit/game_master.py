import streamlit as st
from string import Template
import pymongo
from pymongo.server_api import ServerApi
import pandas as pd

from beer_game.game_repo import GameRepo
from beer_game.mongodb_adapter import MongoDBAdapter
from beer_game.sqlite_adapter import SQLiteAdapter
from beer_game.dict_db_adapter import DictDBAdapter


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
    initial_sidebar_state="expanded"
)


# =========================
# Database Adapter Factory
# =========================
@st.cache_resource
def get_db_adapter():
    db_type = st.secrets.get("db", {}).get("type", "dict")

    if db_type == "mongodb":
        uri = st.secrets.get("db", {}).get("mongodb", {}).get("uri")
        if not uri:
            # Fallback to old config for compatibility
            uri = st.secrets.get("mongo", {}).get("uri")
        if not uri:
            st.error("MongoDB URI not found in secrets.toml")
            st.stop()
        client = pymongo.MongoClient(uri, server_api=ServerApi("1"))
        return MongoDBAdapter(client)
    elif db_type == "sqlite":
        path = st.secrets.get("db", {}).get("sqlite", {}).get("path", "beer_game.db")
        return SQLiteAdapter(path)
    elif db_type == "dict":
        return DictDBAdapter()
    else:
        st.error(f"Invalid db.type '{db_type}' in secrets.toml")
        st.stop()


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
        admin_key == st.secrets.get("admin", {}).get("key")
    )

    if st.button(
        "New Game",
        disabled=(not enabled or not game_id or "game" in st.session_state)
    ):
        db = get_db_adapter()
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

    st.divider()

    st.selectbox(
        "lang",
        ("zh", "en", "ja"),
        index=2,
        key="lang"
    )


# =========================
# Display Functions
# =========================
def game_master():
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
    left, _, mid1, mid2, _, right = st.columns([3,1,3,3,1,3])

    left_c = left.container(
        height=80,
        border=False,
        vertical_alignment="bottom",
    )

    left_c.button(
        "Refresh",
        width="stretch"
    )

    mid1_c = mid1.container(
        height=80,
        border=False,
        vertical_alignment="bottom",
    )

    order = mid1_c.number_input(
        "Order",
        step=1,
        value=0,
        placeholder="Order",
        label_visibility="visible",
        width="stretch"
    )

    mid2_c = mid2.container(
        height=80,
        border=False,
        vertical_alignment="bottom",
    )

    if mid2_c.button(
        "Place Order",
        disabled=(order is None),
        width="stretch"
    ):
        gameRepo.dispatch(order)
        st.success(f"Order {order} dispatched")

    right_c = right.container(
        height=80,
        border=False,
        vertical_alignment="bottom",
    )

    if right_c.button(
        "Next Week",
        width="stretch"
    ):
        gameRepo.nextWeek()
        st.success("Moved to next week")

    # -------- Player Status --------
    players = gameRepo.reloadPlayerStat()
    n_players = len(players)

    n_pending_players = 0
    for player, roles in players.items():
        is_pending = False
        for role_name in ["shop", "retailer", "factory"]:
            role = roles[role_name]
            if role["enabled"] and not role["purchased"]:
                is_pending = True
                break
        if is_pending:
            n_pending_players += 1
    st.text(f"{n_players} players / {n_pending_players} players pending order input")

    tab_names = []
    for player, roles in players.items():
        pending_roles_count = 0
        for role_name in ["shop", "retailer", "factory"]:
            role = roles[role_name]
            if role["enabled"] and not role["purchased"]:
                pending_roles_count += 1
        if pending_roles_count > 0:
            tab_names.append(f"{player} ({pending_roles_count} pending)")
        else:
            tab_names.append(player)

    tabs = st.tabs(tab_names or ["No Player"])

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
            # st.write(roles)

            st.divider()
            st.subheader(f"History - {player}")
            
            from beer_game.player_repo import PlayerRepo, ROLES
            
            h_role = st.selectbox(
                "Role",
                ("shop", "retailer", "factory"),
                key=f"h_role_{player}",
                label_visibility="collapsed"
            )

            p_repo = PlayerRepo(gameRepo.game, player, h_role, gameRepo.db)
            history = p_repo.get_stat_history()
            
            if history:
                start_week = history[0]['week']
                current_week = week
                
                order_history = gameRepo.db.getOrderByWeek(gameRepo.game, start_week, current_week)
                
                table_data = []
                lang = st.session_state.get("lang", "zh")
                
                headers = {
                    "zh": ["週", "注文", "在庫", "在庫切れ", "発注", "コスト"],
                    "en": ["Week", "Incoming Order", "Inventory", "Out of Stock", "Placed Order", "Cost"],
                    "ja": ["週", "注文", "在庫", "在庫切れ", "発注", "コスト"]
                }
                current_headers = headers.get(lang, headers["zh"])

                for h in reversed(history):
                    w = h['week']
                    
                    incoming_order = order_history.get(w, {}).get(player, {}).get(h_role, {}).get('buy', 0)

                    my_placed_order = 0
                    if h_role != "factory": # factory does not place order to next role
                        my_index = ROLES.index(h_role)
                        next_role = ROLES[my_index + 1]
                        my_placed_order = order_history.get(w, {}).get(player, {}).get(next_role, {}).get('buy', 0)
                    
                    table_data.append({
                        current_headers[0]: w,
                        current_headers[1]: incoming_order,
                        current_headers[2]: h['inventory'],
                        current_headers[3]: h['out_of_stock'],
                        current_headers[4]: my_placed_order,
                        current_headers[5]: h['cost']
                    })
                
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No history data available for this role.")


# =========================
# Main Area
# =========================
if "game" in st.session_state:
    game_master()
else:
    lang = st.session_state.get("lang", "zh")
    ANNOUNCE_I18N = {
        "zh": "👈 Enter the required information in the sidebar and start playing.",
        "en": "👈 Enter the required information in the sidebar and start playing.",
        "ja": "👈 サイドバーから必要事項を入力してゲームを始めてください。"
    }
    announce = ANNOUNCE_I18N.get(lang, ANNOUNCE_I18N["zh"])
    st.write(announce)
