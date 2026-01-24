import streamlit as st
from supabase import create_client

# --- Supabase設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]  # Publishable key（anon）
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 商品単価 ---
P_SHIRT, P_PANTS, P_SOCKS = 2000, 3000, 500

# --- Streamlitページ設定 ---
st.set_page_config(page_title="注文登録", layout="wide")

# --- ログインチェック ---
if "user" not in st.session_state:
    st.session_state.user = None

# ログインフォーム
if st.session_state.user is None:
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state.user = res.user
            st.success(f"ようこそ {email}")
        else:
            st.error("ログイン失敗")
    st.stop()  # ログイン前はここで止める

user_id = st.session_state.user.id  # UID取得

# --- 注文フォーム ---
st.title("注文登録")

name = st.text_input("お名前")
shirt_qty = st.number_input("シャツ", 0, 10)
pants_qty = st.number_input("ズボン", 0, 10)
socks_qty = st.number_input("靴下", 0, 10)

total_price = shirt_qty*P_SHIRT + pants_qty*P_PANTS + socks_qty*P_SOCKS
st.write(f"合計金額: {total_price} 円")

if st.button("注文確定"):
    order = {
        "name": name,
        "shirt": shirt_qty,
        "pants": pants_qty,
        "socks": socks_qty,
        "total_price": total_price,
        "user_id": user_id
    }
    res = supabase.table("orders").insert(order).execute()
    if res.data:
        st.success(f"注文完了！ID: {res.data[0]['id']}")
    else:
        st.error("注文失敗")

# --- 自分の注文を一覧表示 ---
st.write("### 自分の注文履歴")
orders = supabase.table("orders").select("*").execute()
if orders.data:
    for o in orders.data:
        st.write(o)
