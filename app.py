import streamlit as st
import requests
from supabase import create_client, Client

# --- 1. Supabase設定 ---
# StreamlitのSecretsに保存した情報を使用
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 商品単価の設定
P_SHIRT = 2000
P_PANTS = 3000
P_SOCKS = 500

st.set_page_config(page_title="注文登録フォーム", layout="centered")
st.title("📦 注文・金額登録")

# --- 2. お届け先情報入力 ---
st.subheader("お届け先情報")
name = st.text_input("お名前")
zipcode = st.text_input("郵便番号 (7桁)")

# 住所検索機能
if st.button("住所を検索"):
    res = requests.get(f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zipcode}").json()
    if res.get("results"):
        r = res["results"][0]
        st.session_state.address_input = f"{r['address1']}{r['address2']}{r['address3']}"
    else:
        st.error("住所が見つかりませんでした。")

address = st.text_input("住所", value=st.session_state.get("address_input", ""))

st.divider()

# --- 3. 数量選択（横並びレイアウト） ---
st.subheader("商品選択")

# シャツ
col1, col2 = st.columns([2, 1])
with col1:
    st.write("### シャツ")
    st.caption(f"単価: {P_SHIRT}円")
with col2:
    shirt = st.selectbox("枚数", options=list(range(11)), key="s_qty", label_visibility="collapsed")

# ズボン
col3, col4 = st.columns([2, 1])
with col3:
    st.write("### ズボン")
    st.caption(f"単価: {P_PANTS}円")
with col4:
    pants = st.selectbox("本数", options=list(range(11)), key="p_qty", label_visibility="collapsed")

# 靴下
col5, col6 = st.columns([2, 1])
with col5:
    st.write("### 靴下")
    st.caption(f"単価: {P_SOCKS}円")
with col6:
    socks = st.selectbox("足数", options=list(range(11)), key="so_qty", label_visibility="collapsed")

# --- 4. プルダウンを「下側」に開かせるための余白 ---
# 選択肢が上に被らないよう、空のコンテナでスペースを作ります
st.container(height=150, border=False)

# --- 5. 金額計算と保存 ---
total_price = (shirt * P_SHIRT) + (pants * P_PANTS) + (socks * P_SOCKS)

st.divider()
st.metric(label="現在の合計金額", value=f"{total_price}円")

if st.button("この内容でデータベースに保存"):
    if name and address:
        try:
            # 各セル（列）に直接データを割り当て
            data = {
                "name": name,
                "zipcode": zipcode,
                "address": address,
                "shirt": shirt,
                "pants": pants,
                "socks": socks,
                "total_price": total_price
            }
            
            # Supabaseのテーブル 'orders' に挿入
            supabase.table("orders").insert(data).execute()
            
            st.success(f"保存完了！ 合計金額: {total_price}円")
            st.balloons()
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.info("Supabaseに shirt, pants, socks, total_price の列が作成されているか確認してください。")
    else:
        st.error("お名前と住所を入力してください。")
