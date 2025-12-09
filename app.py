import streamlit as st
import pandas as pd
import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# --- タイトルと設定 ---
st.title('🍺 代行割り勘 & ルート最適化')
st.caption('誰がどの車に乗って、いくら払うかを計算します')

# --- 入力エリア ---
col1, col2 = st.columns(2)
with col1:
    total_cost = st.number_input('代行料金の総額（予想）', value=10000, step=1000)
with col2:
    driver_capacity = st.number_input('車の定員（運転手除く）', value=3)

# 簡易的な位置情報（本来はGoogle Maps APIで住所から取得）
# ここではサンプルとして大阪の架空の座標を使用
locations = {
    '居酒屋（出発）': {'x': 0, 'y': 0},
    'Aさん宅': {'x': 2, 'y': 5},   # 車の持ち主
    'Bさん宅': {'x': 5, 'y': 2},
    'Cさん宅': {'x': 1, 'y': 8},
    'Dさん宅': {'x': 6, 'y': 6},
}

# 参加者選択
selected_members = st.multiselect(
    '帰るメンバーを選択（最初は車の持ち主を選択してください）',
    options=list(locations.keys())[1:], # 居酒屋以外
    default=['Aさん宅', 'Bさん宅', 'Cさん宅']
)

if not selected_members:
    st.warning('メンバーを選択してください')
    st.stop()

# --- 内部ロジック関数 ---
def calculate_distance(p1, p2):
    return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)

if st.button('ルートと金額を計算する'):
    # データ準備
    active_locs = ['居酒屋（出発）'] + selected_members
    # 車の持ち主（リストの最後の人を所有者と仮定する簡易ロジック）
    car_owner = selected_members[0] 
    
    st.divider()
    st.subheader(f"🚗 {car_owner} の車で帰ります")

    # 距離計算（簡易シミュレーション）
    total_dist = 0
    route_log = []
    
    # ここではOR-Toolsを使わず、簡易的に「近い順」に並べる単純なロジックで代用
    # （本格実装ではここに前回のOR-Toolsコードが入ります）
    current_pos = locations['居酒屋（出発）']
    unvisited = selected_members.copy()
    
    # 車の持ち主は最後
    if car_owner in unvisited:
        unvisited.remove(car_owner)
    
    route = ['居酒屋（出発）']
    
    # 持ち主以外を近い順に回る
    while unvisited:
        nearest = min(unvisited, key=lambda x: calculate_distance(current_pos, locations[x]))
        dist = calculate_distance(current_pos, locations[nearest])
        total_dist += dist
        route.append(nearest)
        route_log.append(f"{route[-2]} ➝ {nearest} ({dist:.1f}km)")
        current_pos = locations[nearest]
        unvisited.remove(nearest)
    
    # 最後に持ち主の家へ
    dist_last = calculate_distance(current_pos, locations[car_owner])
    total_dist += dist_last
    route.append(car_owner)
    route_log.append(f"{route[-2]} ➝ {car_owner} ({dist_last:.1f}km)")
    
    # --- 結果表示 ---
    st.info('**推奨ルート:** ' + ' → '.join(route))
    
    # 割り勘計算（距離比例法）
    st.write("### 💰 お支払い計算")
    
    # 各自の乗車距離を計算
    payment_data = []
    for member in selected_members:
        # 居酒屋からその人が降りるまでの距離
        my_dist = 0
        for i in range(len(route)-1):
            p1 = locations[route[i]]
            p2 = locations[route[i+1]]
            my_dist += calculate_distance(p1, p2)
            if route[i+1] == member:
                break
        
        # 簡易計算： (自分の距離 / 全員の距離の合計) * 総額
        # 注: 本来はもっと複雑ですが、MVPとして簡略化
        payment_data.append({
            "名前": member,
            "乗車距離": f"{my_dist:.1f}",
            "係数": my_dist
        })
    
    df = pd.DataFrame(payment_data)
    total_coefficient = df['係数'].sum()
    
    df['支払額(円)'] = (df['係数'] / total_coefficient * total_cost).astype(int)
    
    st.table(df[['名前', '支払額(円)', '乗車距離']])
    
    st.success(f"合計 {df['支払額(円)'].sum()} 円 （端数誤差あり）")