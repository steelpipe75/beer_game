import streamlit as st

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Beer Game (Home)",
    page_icon="🍺",
    initial_sidebar_state="expanded",
    layout="wide"
)

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.title("Beer Game")
    st.selectbox(
        "lang",
        ("zh", "en", "ja"),
        index=2,
        key="lang"
    )

# =========================
# Main Area
# =========================
def home_ja():
    st.title("🍺 ビールゲームへようこそ")
    
    st.markdown("""
    ビールゲームは、サプライチェーンにおける情報の伝達の遅れや在庫管理の難しさを体験するためのシミュレーションゲームです。
    
    ### 🎮 ゲームの概要
    プレイヤーはサプライチェーンの各拠点（小売、卸売、工場）を担当し、刻々と変化する需要に対応しながら、**在庫コストと欠品コストの合計を最小化すること**を目指します。
    
    ### 🏗️ 担当する役割
    1.  **小売 (Shop):** 消費者に最も近い拠点です。
    2.  **卸売 (Retailer):** 小売からの注文を受け、工場に発注します。
    3.  **工場 (Factory):** 卸売からの注文を受け、ビールを生産（発注）します。
    
    ### 🔄 1週間の流れ
    各プレイヤーは毎週、以下のステップで行動します。
    
    1.  **情報の確認 (Refresh):** 今週届いた入荷量や、受け取った注文量を確認します。
    2.  **発注量の決定 (Order):** 次の週以降の在庫を考慮して、上流の拠点（または生産ライン）への発注量を決めます。
    3.  **発注の実行 (Place Order):** 発注ボタンを押して確定します。
    4.  **週の更新:** 全員の発注が完了すると、ゲームマスターが「Next Week」ボタンを押して次の週に進みます。
    
    ### 💰 コストの計算
    *   **在庫コスト:** 在庫を1つ保持するごとに発生します。
    *   **欠品コスト:** 注文に応えられず、欠品（バックオーダー）が発生した際に、在庫コストよりも高いコストが発生します。
    
    ### 🚀 始め方
    1.  サイドバーのナビゲーションから「Player」または「Game Master」を選択します。
    2.  **プレイヤーの方:** `game_id`, `supply_chain_id`（チーム名など）、`role`（役割）を入力して参加してください。
    3.  **ゲームマスターの方:** 新しいゲームを作成し、各週の進行を管理します。
    """)

def home_en():
    st.title("🍺 Welcome to the Beer Game")
    st.markdown("""
    The Beer Game is a supply chain simulation that demonstrates the difficulties of inventory management and the effects of information delays.
    
    ### 🎮 Game Overview
    Players take roles in a supply chain (Shop, Retailer, Factory) and aim to **minimize the sum of inventory costs and backorder costs** while responding to changing demand.
    
    ### 🏗️ Roles
    1.  **Shop:** The closest node to the end consumer.
    2.  **Retailer:** Receives orders from the Shop and places orders to the Factory.
    3.  **Factory:** Receives orders from the Retailer and "orders" (produces) beer.
    
    ### 🔄 Weekly Flow
    Each week, players follow these steps:
    1.  **Refresh:** Check new arrivals and incoming orders for the week.
    2.  **Order:** Decide how much to order from the upstream node or production.
    3.  **Place Order:** Confirm your order.
    4.  **Next Week:** Once all players have ordered, the Game Master moves the simulation to the next week.
    
    ### 💰 Cost Calculation
    *   **Inventory Cost:** Charged for each unit held in inventory.
    *   **Backorder Cost:** Charged when orders cannot be fulfilled. Usually higher than inventory costs.
    
    ### 🚀 How to Start
    1.  Select "Player" or "Game Master" from the sidebar navigation.
    2.  **Players:** Enter `game_id`, `supply_chain_id`, and your `role` to join.
    3.  **Game Master:** Create a new game and manage the weekly progression.
    """)

def home_zh():
    st.title("🍺 歡迎來到啤酒遊戲")
    st.markdown("""
    啤酒遊戲是一個供應鏈模擬，展示了庫存管理的困難和信息延遲の影響。
    
    ### 🎮 遊戲概述
    玩家在供應鏈中扮演角色（零售、批發、工廠），目標是在應對不斷變化的需求的同時，**最小化庫存成本和欠貨成本的總和**。
    
    ### 🏗️ 角色
    1.  **零售 (Shop):** 最接近最終消費者的節點。
    2.  **批發 (Retailer):** 接收來自零售的訂單，並向工廠訂貨。
    3.  **工廠 (Factory):** 接收來自批發的訂單，並「訂貨」（生產）啤酒。
    
    ### 🔄 每週流程
    每週，玩家遵循以下步驟：
    1.  **刷新 (Refresh):** 查看本週的新到貨和進單。
    2.  **下單 (Order):** 決定向上游節点或生產線訂購多少。
    3.  **確認下單 (Place Order):** 確定您的訂單。
    4.  **下一週:** 所有玩家下單後，遊戲管理員將模擬移動到下一週。
    
    ### 💰 成本計算
    *   **庫存成本:** 庫存中每持有一個單位就會產生。
    *   **欠貨成本:** 當無法滿足訂單時產生。通常高於庫存成本。
    
    ### 🚀 如何開始
    1.  從側邊欄導航中選擇「Player」或「Game Master」。
    2.  **玩家:** 輸入 `game_id`、`supply_chain_id` 和您的 `role` 以加入。
    3.  **遊戲管理員:** 創建新遊戲並管理每週進度。
    """)

lang = st.session_state.get("lang", "zh")
if lang == "ja":
    home_ja()
elif lang == "en":
    home_en()
else:
    home_zh()
