import streamlit as st
import requests
from supabase import create_client, Client

# --- Supabase設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 商品単価
P_SHIRT, P_PANTS, P_SOCKS = 2000, 3000, 500

st.set_page_config(page_title="注文登録", layout="centered")
st.title("💰 注文登録フォーム")

# --- 1. お届け先情報 ---
name = st.text_input("お名前")
zipcode = st.text_input("郵便番号")

if st.button("住所を検索"):
    res = requests.get(f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zipcode}").json()
    if res.get("results"):
        r = res["results"][0]
        st.session_state.address_input = f"{r['address1']}{r['address2']}{r['address3']}"

address = st.text_input("住所", value=st.session_state.get("address_input", ""))

st.divider()

# --- 2. 項目の横にプルダウンを配置 ---
st.subheader("数量選択")

# シャツ
col1, col2 = st.columns([2, 1])
with col1:
    st.write(f"### シャツ")
    st.write(f"単価: {P_SHIRT}円")
with col2:
    shirt = st.selectbox("枚数を選択", options=list(range(11)), key="s_qty")

# ズボン
col3, col4 = st.columns([2, 1])
with col3:
    st.write(f"### ズボン")
    st.write(f"単価: {P_PANTS}円")
with col4:
    pants = st.selectbox("本数を選択", options=list(range(11)), key="p_qty")

# 靴下
col5, col6 = st.columns([2, 1])
with col5:
    st.write(f"### 靴下")
    st.write(f"単価: {P_SOCKS}円")
with col6:
    socks = st.selectbox("足数を選択", options=list(range(11)), key="so_qty")

# --- 金額計算 ---
total_price = (shirt * P_SHIRT) + (pants * P_PANTS) + (socks * P_SOCKS)

st.divider()
st.metric(label="合計金額", value=f"{total_price}円")

# --- 3. 保存処理 ---
if st.button("この内容で保存する"):
    if name and address:
        try:
            data = {
                "name": name,
                "zipcode": zipcode,
                "address": address,
                "shirt": shirt,
                "pants": pants,
                "socks": socks,
                "total_price": total_price
            }
            supabase.table("orders").insert(data).execute()
            st.success("データベースの各セルに保存しました！")
            st.balloons()
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.error("入力が不足しています")
