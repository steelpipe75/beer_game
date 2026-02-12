from string import Template
import pymongo
from pymongo.server_api import ServerApi
import streamlit as st

from beer_game.mongodb_adapter import MongoDB
from beer_game.player_repo import PlayerRepo

st.set_page_config(page_title="Beer Player", page_icon="📈")


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
# Timer Fragment
# =========================
@st.fragment(run_every="1s")
def place_order_timer(order):

    if "timer" not in st.session_state:
        st.session_state.timer = 0

    if "locked" not in st.session_state:
        st.session_state.locked = False

    if st.session_state.timer > 0:
        st.toast(f"{st.session_state.timer}", icon="⚠️")
        st.session_state.timer -= 1
        st.session_state.locked = False
    elif st.session_state.timer == 0:
        st.session_state.locked = True

    if st.button(
        "Place Order",
        disabled=(order is None or st.session_state.locked)
    ):
        st.session_state.player.purchase(order)
        st.success(f"{order} order placed")
        st.session_state.timer = 0


# =========================
# Sidebar
# =========================
with st.sidebar:

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
    player_game = st.text_input(
        "player_game",
        key="player_game",
        disabled=("player" in st.session_state)
    )
    player_id = st.text_input(
        "player_id",
        key="player_id",
        disabled=("player" in st.session_state)
    )

    enabled = (
        player_key == st.secrets["player"]["key"]
    )

    if st.button(
        "Join Game",
        disabled=(not enabled or not player_game or not player_id or not role)
    ):
        client = init_connection()
        db = MongoDB(client)

        st.session_state.player = PlayerRepo(
            player_game,
            player_id,
            role,
            db
        )
        st.session_state.player.register()
        st.success(f"{player_game} joined")

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


# =========================
# Main Game Area
# =========================
if "player" in st.session_state:

    st.markdown("""
### Game Flow
1. Refresh
2. Adjust order number
3. Place Order

⬇️ Start here
""")

    stat = st.session_state.player.reloadStat()

    if st.button("Refresh"):
        if (
            "curr_week" not in st.session_state
            or st.session_state.curr_week != stat["week"]
        ):
            st.session_state.timer = 30
            st.session_state.curr_week = stat["week"]

    order = st.number_input(
        "Order",
        step=1,
        value=None,
        placeholder="Order",
        label_visibility="collapsed"
    )

    place_order_timer(order)

    st.markdown(display_stat(stat))
    st.write(tell_story(stat))
