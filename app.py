import streamlit as st
import requests
from supabase import create_client, Client

# --- Supabase設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 商品ごとの単価（計算用）
PRICES = {"shirt": 2000, "pants": 3000, "socks": 500}

st.set_page_config(page_title="注文登録", layout="centered")
st.title("📦 注文登録（プルダウン形式）")

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

# --- 商品入力（プルダウン形式） ---
# options=list(range(11)) で 0〜10 の選択肢を作ります
shirt = st.selectbox("シャツの枚数", options=list(range(11)), index=0)
pants = st.selectbox("ズボンの本数", options=list(range(11)), index=0)
socks = st.selectbox("靴下の足数", options=list(range(11)), index=0)

# 合計金額の計算
total_price = (shirt * PRICES["shirt"]) + (pants * PRICES["pants"]) + (socks * PRICES["socks"])

st.divider()
st.metric(label="合計金額", value=f"{total_price}円")

# --- 保存処理 ---
if st.button("この内容で保存"):
    if name and address:
        try:
            # 💡 エラーの原因だった 'item_name' は含めず、各列に直接入れます
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
            st.success("各セルへ正常に保存されました！")
            st.balloons()
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.info("Supabaseのテーブルに shirt, pants, socks, total_price 列があるか確認してください。")
    else:
        st.error("名前と住所を入力してください。")
