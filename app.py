import streamlit as st
import requests
from supabase import create_client, Client

# --- 1. Supabase設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 単価設定
P_SHIRT, P_PANTS, P_SOCKS = 2000, 3000, 500

# ページ設定
st.set_page_config(page_title="注文登録", layout="centered")

# --- 【重要】ページ遷移の管理 ---
if "submitted" not in st.session_state:
    st.session_state.submitted = False  # まだ確定していない状態

# --- A. 完了画面の表示 ---
if st.session_state.submitted:
    st.title("注文完了")
    st.success("ご注文ありがとうございました。以上です。")
    if st.button("新しい注文を登録する"):
        st.session_state.submitted = False
        st.rerun()

# --- B. 入力画面の表示 ---
else:
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

    # 数量選択
    col1, col2 = st.columns([2, 1])
    with col1: st.write("### シャツ")
    with col2: shirt = st.selectbox("枚数", options=list(range(11)), key="s_qty", label_visibility="collapsed")

    col3, col4 = st.columns([2, 1])
    with col3: st.write("### ズボン")
    with col4: pants = st.selectbox("本数", options=list(range(11)), key="p_qty", label_visibility="collapsed")

    col5, col6 = st.columns([2, 1])
    with col5: st.write("### 靴下")
    with col6: socks = st.selectbox("足数", options=list(range(11)), key="so_qty", label_visibility="collapsed")

    st.divider()
    total_price = (shirt * P_SHIRT) + (pants * P_PANTS) + (socks * P_SOCKS)
    st.metric(label="合計金額", value=f"{total_price}円")

    # 保存ボタン
    if st.button("この内容で確定する。", use_container_width=True):
        if name and address:
            try:
                data = {
                    "name": name, "zipcode": zipcode, "address": address,
                    "shirt": shirt, "pants": pants, "socks": socks, "total_price": total_price
                }
                supabase.table("orders").insert(data).execute()
                
                # ★ここがポイント：フラグをTrueにして再描画
                st.session_state.submitted = True
                st.rerun() 
                
            except Exception as e:
                st.error(f"エラー: {e}")
        else:
            st.error("未入力項目があります。")

    # 底上げ余白（入力中のみ表示）
    st.container(height=400, border=False)
