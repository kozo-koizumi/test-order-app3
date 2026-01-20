import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client

# --- Supabase設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="注文票アプリ", layout="centered")
st.title("注文・住所入力アプリ")

# --- 1. お届け先情報入力 ---
st.subheader("🚚 お届け先情報")
name = st.text_input("お名前")
zipcode = st.text_input("郵便番号 (7桁)", max_chars=7)

if "address_input" not in st.session_state:
    st.session_state.address_input = ""

if st.button("住所を検索"):
    if len(zipcode) == 7:
        url = f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zipcode}"
        res = requests.get(url).json()
        if res.get("results"):
            r = res["results"][0]
            st.session_state.address_input = f"{r['address1']}{r['address2']}{r['address3']}"
        else:
            st.error("住所が見つかりませんでした。")

final_address = st.text_input("住所詳細（番地など）", value=st.session_state.address_input)

st.divider()

# --- 2. 商品選択（プルダウン形式） ---
st.subheader("👕 ご注文内容")

# 商品リストと単価
ITEMS = {
    "シャツ": 2000,
    "ズボン": 3000,
    "靴下": 500
}

order_list = []
total_price = 0

# 商品ごとに個数選択を表示
for item, price in ITEMS.items():
    # 横並びにする
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**{item}** ({price}円)")
    with col2:
        # 0〜10のプルダウン。商品名をkeyに含めるのがポイント
        count = st.selectbox(f"個数", options=list(range(11)), key=f"select_{item}")
    
    if count > 0:
        order_list.append(f"{item} x{count}")
        total_price += price * count

# 合計金額を大きく表示
st.divider()
st.metric(label="合計金額", value=f"{total_price}円")

# --- 3. 保存処理 ---
if st.button("データをSupabaseへ保存"):
    if not order_list:
        st.error("商品が1つも選ばれていません。")
    elif name and final_address:
        try:
            # 注文内容を1つの文字列にまとめる（例: "シャツ x1, ズボン x2"）
            item_summary = ", ".join(order_list)
            
            data = {
                "name": name,
                "zipcode": zipcode,
                "address": final_address,
                "item_name": item_summary,   # 👈 Supabaseに列を追加してね
                "total_price": total_price   # 👈 Supabaseに列を追加してね
            }
            
            # ordersテーブルに挿入
            response = supabase.table("orders").insert(data).execute()
            st.success(f"保存完了！ 内容: {item_summary}")
            st.balloons() # お祝いの風船を表示
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    else:
        st.error("お名前と住所を入力してください。")
