import streamlit as st
import requests
from supabase import create_client, Client

# --- 1. Supabase設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 単価設定
P_SHIRT, P_PANTS, P_SOCKS = 2000, 3000, 500

st.set_page_config(page_title="注文登録", layout="centered")

# --- 2. お届け先情報（上部に配置） ---
st.title("注文登録")
name = st.text_input("お名前")
zipcode = st.text_input("郵便番号 (7桁)")

if st.button("住所を検索"):
    res = requests.get(f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zipcode}").json()
    if res.get("results"):
        r = res["results"][0]
        st.session_state.address_input = f"{r['address1']}{r['address2']}{r['address3']}"

address = st.text_input("住所", value=st.session_state.get("address_input", ""))

st.divider()

# --- 3. 数量選択（ここをページの中央に配置） ---
# 下に「合計金額」や「ボタン」などの要素がたくさん並ぶようにして、
# プルダウンが下に開くためのスペースを物理的に確保します。

col1, col2 = st.columns([2, 1])
with col1: st.write("### シャツ")
with col2: shirt = st.selectbox("枚数", options=list(range(11)), key="s_qty", label_visibility="collapsed")

col3, col4 = st.columns([2, 1])
with col3: st.write("### ズボン")
with col4: pants = st.selectbox("本数", options=list(range(11)), key="p_qty", label_visibility="collapsed")

col5, col6 = st.columns([2, 1])
with col5: st.write("### 靴下")
with col6: socks = st.selectbox("足数", options=list(range(11)), key="so_qty", label_visibility="collapsed")

# --- 4. 金額表示と保存ボタン（ここを長くして余白を作る） ---
st.divider()

# 合計金額のリアルタイム計算
total_price = (shirt * P_SHIRT) + (pants * P_PANTS) + (socks * P_SOCKS)

# 金額表示
st.metric(label="合計金額", value=f"{total_price}円")

# 保存ボタン
if st.button("この内容で保存する", use_container_width=True):
    if name and address:
        try:
            data = {
                "name": name, "zipcode": zipcode, "address": address,
                "shirt": shirt, "pants": pants, "socks": socks, "total_price": total_price
            }
            supabase.table("orders").insert(data).execute()
            st.success("ご注文ありがとうございました。以上です。")
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.error("未入力項目があります。")

# --- 5. 強制的な底上げ余白 ---
# これがあることで、上のプルダウンをクリックした時に「下にスペースがある」とブラウザが認識します
st.container(height=400, border=False)
