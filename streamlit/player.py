from string import Template
import pymongo
from pymongo.server_api import ServerApi
import streamlit as st

from beer_game.mongodb_adapter import MongoDBAdapter
from beer_game.sqlite_adapter import SQLiteAdapter
from beer_game.dict_db_adapter import DictDBAdapter
from beer_game.player_repo import PlayerRepo


# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Beer Game (Player)",
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
# Timer Fragment
# =========================
@st.fragment(run_every="1s")
def place_order_timer(order):
    order_place = False

    if "timer" not in st.session_state:
        st.session_state.timer = 0

    if "locked" not in st.session_state:
        st.session_state.locked = False

    if st.session_state.timer > 0:
        st.toast(f"{st.session_state.timer}", icon="⚠️")
        st.session_state.timer -= 1
        st.session_state.locked = False
    elif st.session_state.timer == 0:
        if not st.session_state.locked:
            order_place = True
        st.session_state.locked = True

    if st.button(
        "Place Order",
        disabled=(order is None or st.session_state.locked),
        width="stretch"
    ):
        order_place = True
        st.session_state.timer = 0
        st.session_state.locked = True

    if order_place:
        st.session_state.player.purchase(order)
        st.rerun()


# =========================
# Sidebar
# =========================
with st.sidebar:
    st.title("Player")

    role = st.selectbox(
        "player_role",
        ("shop", "retailer", "factory"),
        key="player_role",
        disabled=("player" in st.session_state)
    )

    player_key = st.text_input(
        "player_key",
        type="password",
        key="player_key",
        disabled=("player" in st.session_state)
    )
    game_id = st.text_input(
        "game_id",
        key="game_id",
        disabled=("player" in st.session_state)
    )
    supply_chain_id = st.text_input(
        "supply_chain_id",
        key="supply_chain_id",
        disabled=("player" in st.session_state)
    )

    enabled = (
        player_key == st.secrets.get("player", {}).get("key")
    )

    if st.button(
        "Join Game",
        disabled=(not enabled or not game_id or not supply_chain_id or not role)
    ):
        db = get_db_adapter()

        st.session_state.player = PlayerRepo(
            game_id,
            supply_chain_id,
            role,
            db
        )
        st.session_state.player.register()
        st.success(f"{game_id} joined")

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
def display_stat(stat):
    lang = st.session_state.get("lang", "zh")

    STAT_I18N = {
        "zh": """# $role 's Week $week
| Order | Inventoy | Out of Stock | Cost |
|------|-------| ----- | ----- |
|$order | $inventory | $out_of_stock | $cost |
""",
        "en": """# $role 's Week $week
| Order | Inventoy | Out of Stock | Cost |
|------|-------| ----- | ----- |
|$order | $inventory | $out_of_stock | $cost |
""",
        "ja": """# $role 's Week $week
| 注文 | 在庫 | 在庫切れ | コスト |
|------|-------| ----- | ----- |
|$order | $inventory | $out_of_stock | $cost |
""",
    }

    template = Template(STAT_I18N.get(lang, STAT_I18N["zh"]))
    return template.substitute(
        stat | {
            "role": st.session_state.player_role.capitalize()
        }
    )


def tell_story(stat):
    lang = st.session_state.get("lang", "zh")

    STORY_I18N = {
        "zh": """你本週到貨 $delivery 加上原有庫存 $inventory_this_week 共可賣 $can_sell

本週進單 $order 加上積壓貨單 $out_of_stock_this_week 共需賣 $should_sell

因此，賣出 $sell 並使庫存為 $inventory

最終，總成本是 $cost""",
        "en": """You have $delivery new arrivals this week plus $inventory_this_week original inventory, totaling $can_sell available for sale

This week's orders $order plus backlogged orders $out_of_stock_this_week sum up to $should_sell that need to be sold

Therefore, you sell $sell and your inventory becomes $inventory

Finally, the total cost is $cost""",
        "ja": """今週の入荷 $delivery と既存の在庫 $inventory_this_week を合わせて、合計 $can_sell 販売可能です。

今週の注文 $order と滞留注文 $out_of_stock_this_week を合わせて、合計 $should_sell を販売する必要があります。

したがって、$sell を販売し、在庫は $inventory になります。

最終的な総コストは $cost です。"""
    }

    template = Template(STORY_I18N.get(lang, STORY_I18N["zh"]))
    return template.substitute(stat)


def player():
    st.markdown("""
### Game Flow
1. Refresh
2. Adjust order number
3. Place Order

⬇️ Start here
""")

    stat = st.session_state.player.reloadStat()

    left, _, mid, right = st.columns([3,1,6,6])

    left_c = left.container(
        height=80,
        border=False,
        vertical_alignment="bottom",
    )

    if left_c.button(
        "Refresh",
        width="stretch"
    ):
        if (
            "curr_week" not in st.session_state
            or st.session_state.curr_week != stat["week"]
        ):
            st.session_state.timer = 30
            st.session_state.curr_week = stat["week"]

    mid_c = mid.container(
        height=80,
        border=False,
        vertical_alignment="bottom",
    )

    order = mid_c.number_input(
        "Order",
        step=1,
        value=0,
        placeholder="Order",
        label_visibility="visible",
        width="stretch"
    )

    right_c = right.container(
        height=80,
        border=False,
        vertical_alignment="bottom",
    )

    with right_c:
        place_order_timer(order)

    with st.container(height=80, border=False):
        if st.session_state.locked:
            st.success(f"{order} order placed")

    st.markdown(display_stat(stat))
    st.write(tell_story(stat))


# =========================
# Main Area
# =========================
if "player" in st.session_state:
    player()
else:
    lang = st.session_state.get("lang", "zh")
    ANNOUNCE_I18N = {
        "zh": "👈 Enter the required information in the sidebar and start playing.",
        "en": "👈 Enter the required information in the sidebar and start playing.",
        "ja": "👈 サイドバーから必要事項を入力してゲームを始めてください。"
    }
    announce = ANNOUNCE_I18N.get(lang, ANNOUNCE_I18N["zh"])
    st.write(announce)
