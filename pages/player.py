from string import Template
import pymongo
from pymongo.server_api import ServerApi
import streamlit as st

from beer_game.mongodb_adapter import MongoDB
from beer_game.player_repo import PlayerRepo

st.set_page_config(page_title="Beer Player", page_icon="📈")

@st.fragment(run_every="1s")
def place_order_timer():
    if "timer" not in st.session_state:
        st.session_state.locked = False
    elif st.session_state.timer > 0:
        st.toast(f"{st.session_state.timer}", icon="⚠️")

        st.session_state.timer -= 1
        st.session_state.locked = False
    else:
        st.session_state.locked = True

    if st.button("Place Order", disabled=(
            not order or st.session_state.locked
        )):
        st.session_state.player.purchase(order)
        st.write(f"{order} order placed")
        st.session_state.timer = 0

@st.cache_resource
def init_connection():
    return pymongo.MongoClient(
        st.secrets["mongo"]["uri"],
        server_api=ServerApi('1')
        )

if "selectbox" not in st.session_state:
    def selectbox(k, ops):
        if not st.session_state.check_state(k):
            st.session_state[k] = st.selectbox(
                k,
                ops,
                index=None
            )
        else:
            st.selectbox(
                k,
                [],
                index=None,
                placeholder=st.session_state[k],
                disabled=True
            )

    st.session_state.selectbox = selectbox



with st.sidebar:
    st.session_state.selectbox("player_role", ("shop", "retailer", "factory"))
    st.session_state.text_input("player_key", True)

    enabled = (
        st.session_state.player_key == st.secrets["player"]["key"]
    )

    st.session_state.text_input("player_game")
    st.session_state.text_input("player_id")

    role = st.session_state.player_role
    game = st.session_state.player_game
    player = st.session_state.player_id

    if st.button("Join Game", disabled=(not enabled or not player \
                                         or not game or not role)):
        st.write(f"{game} joined")
        client = init_connection()
        db = MongoDB(client)
        st.session_state.player = PlayerRepo(
            game,
            player,
            role,
            db
        )
        st.session_state.player.register()

    st.divider()
    st.session_state.selectbox("lang", ("zh", "en", "ja"))


def display_stat(stat, lang='zh'):
    if "lang" in st.session_state:
        lang = st.session_state.lang

    STAT_I18N = {
        'zh': '''# $role 's Week $week
| Order | Inventoy | Out of Stock | Cost |
|------|-------| ----- | ----- |
|$order | $inventory | $out_of_stock | $cost |
''',
        'en': '''# $role 's Week $week
| Order | Inventoy | Out of Stock | Cost |
|------|-------| ----- | ----- |
|$order | $inventory | $out_of_stock | $cost |
''',
        'ja': '''# $role 's Week $week
| 注文 | 在庫 | 在庫切れ | コスト |
|------|-------| ----- | ----- |
|$order | $inventory | $out_of_stock | $cost |
''',
}
    STAT = Template(STAT_I18N.get(lang) or STAT_I18N['zh'])
    return STAT.substitute(stat | {
        'role': st.session_state.player_role.capitalize()
        })


def tell_story(stat, lang='zh'):
    if "lang" in st.session_state:
        lang = st.session_state.lang

    STORY_I18N = {
        'zh': '''你本週到貨 $delivery 加上原有庫存 $inventory_this_week 共可賣 $can_sell

本週進單 $order 加上積壓貨單 $out_of_stock_this_week 共需賣 $should_sell

因此，賣出 $sell 並使庫存為 $inventory

最終，總成本是 $cost''',
        'en': '''You have $delivery new arrivals this week plus $inventory_this_week original inventory, totaling $can_sell available for sale

This week's orders $order plus backlogged orders $out_of_stock_this_week sum up to $should_sell that need to be sold

Therefore, you sell $sell and your inventory becomes $inventory

Finally, the total cost is $cost''',
        'ja': '''今週の入荷 $delivery と既存の在庫 $inventory_this_week を合わせて、合計 $can_sell 販売可能です。

今週の注文 $order と滞留注文 $out_of_stock_this_week を合わせて、合計 $should_sell を販売する必要があります。

したがって、$sell を販売し、在庫は $inventory になります。

最終的な総コストは $cost です。'''
    }
    STORY = Template(STORY_I18N.get(lang) or STORY_I18N['zh'])
    return STORY.substitute(stat)

if st.session_state.check_state("player"):
    st.markdown('''Game Flow
1. Refresh
2. Adjust order number
3. Place Order

⬇️ Start here
''')
    stat = st.session_state.player.reloadStat()

    if st.button("Refresh"):
        if "curr_week" not in st.session_state or st.session_state.curr_week != stat['week']:
            st.session_state.timer = 30
            st.session_state.curr_week = stat['week']


    order = st.number_input(
        "Order",
        value=None,
        step=1,
        label_visibility="collapsed",
        placeholder="Order"
    )

    place_order_timer()

    st.markdown(display_stat(stat))
    st.write(tell_story(stat))