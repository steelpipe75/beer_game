import streamlit as st
from string import Template
import pymongo
from pymongo.server_api import ServerApi
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    initial_sidebar_state="expanded",
    layout="wide"
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
            
            all_history_data = []
            min_week = week
            
            for h_role in ["shop", "retailer", "factory"]:
                p_repo = PlayerRepo(gameRepo.game, player, h_role, gameRepo.db)
                h_list = p_repo.get_stat_history()
                if h_list:
                    min_week = min(min_week, h_list[0]['week'])
                    all_history_data.append((h_role, h_list))
            
            if all_history_data:
                start_week = min_week
                current_week = week
                
                order_history = gameRepo.db.getOrderByWeek(gameRepo.game, start_week, current_week)
                
                lang = st.session_state.get("lang", "zh")
                
                # 多言語対応のマップ
                role_names_map = {
                    "zh": {"shop": "零售", "retailer": "批發", "factory": "工廠"},
                    "en": {"shop": "Shop", "retailer": "Retailer", "factory": "Factory"},
                    "ja": {"shop": "小売", "retailer": "卸売", "factory": "工場"}
                }
                metric_names_map = {
                    "zh": ["訂單", "庫存", "欠貨", "下單", "成本"],
                    "en": ["Order", "Inv", "OoS", "Buy", "Cost"],
                    "ja": ["注文", "在庫", "欠品", "発注", "コスト"]
                }
                total_cost_label_map = {
                    "zh": "総成本",
                    "en": "Total Cost",
                    "ja": "合計コスト"
                }
                
                curr_role_map = role_names_map.get(lang, role_names_map["en"])
                curr_metrics = metric_names_map.get(lang, metric_names_map["en"])
                total_cost_label = total_cost_label_map.get(lang, total_cost_label_map["en"])
                target_roles = ["shop", "retailer", "factory"]

                # MultiIndex の列定義を作成
                col_tuples = []
                for r_key in target_roles:
                    r_name = curr_role_map[r_key]
                    for m in curr_metrics:
                        col_tuples.append((r_name, m))
                
                # 合計コスト用の列を追加（トップレベルは空文字列または適切なラベル）
                col_tuples.append((total_cost_label, ""))
                
                cols = pd.MultiIndex.from_tuples(col_tuples)
                weeks = sorted(range(start_week, current_week + 1), reverse=True)
                
                # データを格納する DataFrame の初期化
                df = pd.DataFrame(index=weeks, columns=cols)
                df.index.name = "Week" if lang == "en" else "週"
                
                for w in weeks:
                    weekly_total_cost = 0
                    for h_role, h_list in all_history_data:
                        if h_role not in curr_role_map: continue
                        
                        h = next((x for x in h_list if x['week'] == w), None)
                        if not h: continue
                        
                        r_name = curr_role_map[h_role]
                        
                        # データの取得
                        incoming_order = order_history.get(w, {}).get(player, {}).get(h_role, {}).get('buy', 0)
                        my_placed_order = 0
                        if h_role != "factory":
                            my_index = ROLES.index(h_role)
                            next_role = ROLES[my_index + 1]
                            my_placed_order = order_history.get(w, {}).get(player, {}).get(next_role, {}).get('buy', 0)

                        # 各セルに値をセット
                        df.loc[w, (r_name, curr_metrics[0])] = incoming_order
                        df.loc[w, (r_name, curr_metrics[1])] = h['inventory']
                        df.loc[w, (r_name, curr_metrics[2])] = h['out_of_stock']
                        df.loc[w, (r_name, curr_metrics[3])] = my_placed_order
                        df.loc[w, (r_name, curr_metrics[4])] = h['cost']
                        
                        weekly_total_cost += h['cost']
                    
                    # 週ごとの合計コストをセット
                    df.loc[w, (total_cost_label, "")] = weekly_total_cost
                
                st.dataframe(df, width="stretch")

                # Plotly subplot chart for Game Master
                if not df.empty:
                    # Sort by week (index) for chronological order
                    df_plot = df.sort_index()
                    x_axis_name = df_plot.index.name or "Week"
                    
                    # Create subplots
                    fig = make_subplots(
                        rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.1,
                        subplot_titles=("Metrics", "Cost")
                    )

                    # Distinguish between Metric and Cost columns
                    cost_metric_name = curr_metrics[4] # "Cost" / "コスト" / "成本"
                    
                    # Standard colors
                    colors = px.colors.qualitative.Plotly
                    color_idx = 0

                    for col in df_plot.columns:
                        role_name, metric_name = col
                        is_total_cost = (role_name == total_cost_label)
                        is_role_cost = (metric_name == cost_metric_name)
                        
                        trace_name = f"{role_name} {metric_name}".strip()
                        
                        if is_total_cost or is_role_cost:
                            # Add to Cost subplot (Row 2)
                            fig.add_trace(
                                go.Scatter(
                                    x=df_plot.index,
                                    y=df_plot[col],
                                    name=trace_name,
                                    mode='lines+markers',
                                    line=dict(width=3 if is_total_cost else 1, color='red' if is_total_cost else None)
                                ),
                                row=2, col=1
                            )
                        else:
                            # Add to Metrics subplot (Row 1)
                            fig.add_trace(
                                go.Scatter(
                                    x=df_plot.index,
                                    y=df_plot[col],
                                    name=trace_name,
                                    mode='lines+markers'
                                ),
                                row=1, col=1
                            )

                    fig.update_xaxes(type='category', title_text=x_axis_name, row=2, col=1)
                    fig.update_layout(
                        height=700,
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
                    )

                    st.plotly_chart(fig, width="stretch")
            else:
                st.info("No history data available for this supply chain.")


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
