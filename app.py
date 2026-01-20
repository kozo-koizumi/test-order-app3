import streamlit as st
import requests
from supabase import create_client, Client

# --- Supabase設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 商品ごとの単価設定 ---
PRICES = {
    "shirt": 2000,
    "pants": 3000,
    "socks": 500
}

st.set_page_config(page_title="注文登録", layout="centered")
st.title("💰 注文・金額計算フォーム")

# --- お届け先情報 ---
name = st.text_input("お名前")
zipcode = st.text_input("郵便番号 (7桁)")

if st.button("住所を検索"):
    res = requests.get(f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zipcode}").json()
    if res.get("results"):
        r = res["results"][0]
        st.session_state.address_input = f"{r['address1']}{r['address2']}{r['address3']}"

address = st.text_input("住所", value=st.session_state.get("address_input", ""))

st.divider()

# --- 商品入力 ---
st.subheader("数量を入力してください")
shirt = st.number_input(f"シャツ (単価:{PRICES['shirt']}円)", min_value=0, step=1, value=0)
pants = st.number_input(f"ズボン (単価:{PRICES['pants']}円)", min_value=0, step=1, value=0)
socks = st.number_input(f"靴下 (単価:{PRICES['socks']}円)", min_value=0, step=1, value=0)

# --- 金額の自動計算 ---
total_price = (shirt * PRICES["shirt"]) + (pants * PRICES["pants"]) + (socks * PRICES["socks"])

# 合計金額を大きく表示
st.divider()
st.metric(label="今回の合計金額", value=f"{total_price}円")

# --- 保存処理 ---
if st.button("この内容で注文を確定"):
    if name and address:
        if total_price == 0:
            st.warning("商品が選択されていません。")
        else:
            try:
                # 各セル（列）にデータを振り分け
                data = {
                    "name": name,
                    "zipcode": zipcode,
                    "address": address,
                    "shirt": shirt,
                    "pants": pants,
                    "socks": socks,
                    "total_price": total_price  # 👈 合計金額も保存！
                }
                
                # 保存実行
                supabase.table("orders").insert(data).execute()
                
                st.success(f"合計 {total_price}円 で保存しました！")
                st.balloons()
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.info("Supabaseに total_price 列（int8型）があるか確認してください。")
    else:
        st.error("名前と住所を入力してください。")
