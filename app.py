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

# --- ページ遷移の管理 ---
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# --- A. 完了画面の表示 ---
if st.session_state.submitted:
    st.title("注文完了")
    st.success("ご注文ありがとうございました。")
    if st.button("新しい注文を登録する"):
        st.session_state.submitted = False
        st.rerun()

# --- B. 入力画面の表示 ---
else:
    st.title("注文登録")
    
    # 1. 基本情報入力
    name = st.text_input("お名前（必須）")
    zipcode = st.text_input("郵便番号（必須・7桁ハイフンなし）")
    
    if st.button("住所を検索"):
        clean_zipcode = zipcode.replace("-", "").replace(" ", "")
        if len(clean_zipcode) == 7:
            res = requests.get(f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={clean_zipcode}").json()
            if res.get("results"):
                r = res["results"][0]
                st.session_state.address_input = f"{r['address1']}{r['address2']}{r['address3']}"
            else:
                st.error("該当する住所が見つかりませんでした。")

    address = st.text_input("住所（必須）", value=st.session_state.get("address_input", ""))
    phone = st.text_input("電話番号（任意）", placeholder="09012345678")
    email = st.text_input("メールアドレス（任意）", placeholder="example@mail.com")

    st.divider()

    # 2. 商品選択（個数見出しとサイズ入力の追加）
    st.write("### 商品選択")

    # ヘッダー代わり
    h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
    with h_col1: st.write("**商品名**")
    with h_col2: st.write("**個数**")
    with h_col3: st.write("**サイズ**")

    # シャツ
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.write(f"シャツ (¥{P_SHIRT:,})")
    with col2: shirt_qty = st.selectbox("枚数", options=list(range(11)), key="s_qty", label_visibility="collapsed")
    with col3: shirt_size = st.text_input("シャツサイズ", placeholder="例: M", key="s_size", label_visibility="collapsed")

    # ズボン
    col4, col5, col6 = st.columns([2, 1, 1])
    with col4: st.write(f"ズボン (¥{P_PANTS:,})")
    with col5: pants_qty = st.selectbox("本数", options=list(range(11)), key="p_qty", label_visibility="collapsed")
    with col6: pants_size = st.text_input("ズボンサイズ", placeholder="例: L", key="p_size", label_visibility="collapsed")

    # 靴下
    col7, col8, col9 = st.columns([2, 1, 1])
    with col7: st.write(f"靴下 (¥{P_SOCKS:,})")
    with col8: socks_qty = st.selectbox("足数", options=list(range(11)), key="so_qty", label_visibility="collapsed")
    with col9: socks_size = st.text_input("靴下サイズ", placeholder="例: 24-26", key="so_size", label_visibility="collapsed")

    st.divider()
    
    # 3. 合計表示
    total_price = (shirt_qty * P_SHIRT) + (pants_qty * P_PANTS) + (socks_qty * P_SOCKS)
    st.metric(label="合計金額", value=f"{total_price:,}円")

    # 4. 保存ボタン
    if st.button("この内容で確定する", use_container_width=True):
        if name and address and total_price > 0:
            try:
                data = {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "zipcode": zipcode.replace("-", ""),
                    "address": address,
                    "shirt": shirt_qty,
                    "shirt_size": shirt_size, # サイズ追加
                    "pants": pants_qty,
                    "pants_size": pants_size, # サイズ追加
                    "socks": socks_qty,
                    "socks_size": socks_size, # サイズ追加
                    "total_price": total_price
                }
                supabase.table("orders").insert(data).execute()
                st.session_state.submitted = True
                st.rerun() 
            except Exception as e:
                st.error(f"データベースエラー: {e}")
        else:
            st.error("「お名前」「住所」を入力し、商品を1つ以上選択してください。")

    st.container(height=100, border=False)
