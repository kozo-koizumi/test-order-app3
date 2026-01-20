import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client

# --- Supabase設定 ---
# 本来は st.secrets に入れるべき情報です
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="注文票アプリ", layout="centered")
st.title("住所入力・Supabase保存アプリ")

st.subheader("お届け先情報入力")

name = st.text_input("お名前")
zipcode = st.text_input("郵便番号 (7桁)", max_chars=7)

if "address_input" not in st.session_state:
    st.session_state.address_input = ""

# 住所検索ロジック
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

# --- 保存処理 ---
if st.button("データをSupabaseへ保存"):
    if name and final_address:
        try:
            # Supabaseへのインサート処理
            data = {
                "name": name,
                "zipcode": zipcode,
                "address": final_address
            }
            # ordersテーブルに挿入
            response = supabase.table("orders").insert(data).execute()
            
            st.success("Supabaseに保存しました！")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    else:
        st.error("お名前と住所を入力してください。")
