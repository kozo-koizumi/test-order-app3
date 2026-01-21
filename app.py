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

# --- 状態管理の初期化 ---
# phase: "input" (入力), "confirm" (確認), "complete" (完了)
if "phase" not in st.session_state:
    st.session_state.phase = "input"
if "order_data" not in st.session_state:
    st.session_state.order_data = {}

# --- A. 完了画面 ---
if st.session_state.phase == "complete":
    st.title("注文完了")
    st.success("ご注文ありがとうございました。")
    if st.button("新しい注文を登録する"):
        st.session_state.phase = "input"
        st.session_state.order_data = {}
        st.rerun()

# --- B. 確認画面 ---
elif st.session_state.phase == "confirm":
    st.title("注文内容の確認")
    st.info("以下の内容でよろしければ「確定する」を押してください。")
    
    data = st.session_state.order_data
    
    col_info, col_order = st.columns(2)
    with col_info:
        st.markdown("### お届先情報")
        st.write(f"**お名前:** {data['name']}")
        st.write(f"**郵便番号:** {data['zipcode']}")
        st.write(f"**住所:** {data['address']}")
        st.write(f"**電話番号:** {data['phone'] if data['phone'] else '未入力'}")
        st.write(f"**メール:** {data['email'] if data['email'] else '未入力'}")

    with col_order:
        st.markdown("### 注文商品")
        if data['shirt'] > 0: st.write(f"シャツ: {data['shirt']}枚 ({data['shirt_size']})")
        if data['pants'] > 0: st.write(f"ズボン: {data['pants']}本 ({data['pants_size']})")
        if data['socks'] > 0: st.write(f"靴下: {data['socks']}足 ({data['socks_size']})")
        st.markdown(f"**合計金額: {data['total_price']:,}円**")

    st.divider()
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("修正する", use_container_width=True):
            st.session_state.phase = "input"
            st.rerun()
            
    with btn_col2:
        if st.button("確定する", type="primary", use_container_width=True):
            try:
                supabase.table("orders").insert(data).execute()
                st.session_state.phase = "complete"
                st.rerun()
            except Exception as e:
                st.error(f"データベースエラー: {e}")

# --- C. 入力画面 ---
else:
    st.title("注文登録")
    
    # 1. 基本情報入力
    name = st.text_input("お名前（必須）", value=st.session_state.order_data.get("name", ""))
    zipcode = st.text_input("郵便番号（必須・7桁ハイフンなし）", value=st.session_state.order_data.get("zipcode", ""))
    
    if st.button("住所を検索"):
        clean_zipcode = zipcode.replace("-", "").replace(" ", "")
        if len(clean_zipcode) == 7:
            res = requests.get(f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={clean_zipcode}").json()
            if res.get("results"):
                r = res["results"][0]
                st.session_state.address_input = f"{r['address1']}{r['address2']}{r['address3']}"
            else:
                st.error("該当する住所が見つかりませんでした。")

    # 初期値の設定ロジック
    default_address = st.session_state.get("address_input", st.session_state.order_data.get("address", ""))
    address = st.text_input("住所（必須）", value=default_address)
    
    phone = st.text_input("電話番号（任意）", value=st.session_state.order_data.get("phone", ""), placeholder="09012345678")
    email = st.text_input("メールアドレス（任意）", value=st.session_state.order_data.get("email", ""), placeholder="example@mail.com")

    st.divider()

    # 2. 商品選択
    st.write("### 商品選択")
    h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
    with h_col1: st.write("**商品名**")
    with h_col2: st.write("**個数**")
    with h_col3: st.write("**サイズ**")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.write(f"シャツ (¥{P_SHIRT:,})")
    with col2: shirt_qty = st.selectbox("枚数", options=list(range(11)), index=st.session_state.order_data.get("shirt", 0), key="s_qty", label_visibility="collapsed")
    with col3: shirt_size = st.text_input("シャツサイズ", value=st.session_state.order_data.get("shirt_size", ""), placeholder="例: M", key="s_size", label_visibility="collapsed")

    col4, col5, col6 = st.columns([2, 1, 1])
    with col4: st.write(f"ズボン (¥{P_PANTS:,})")
    with col5: pants_qty = st.selectbox("本数", options=list(range(11)), index=st.session_state.order_data.get("pants", 0), key="p_qty", label_visibility="collapsed")
    with col6: pants_size = st.text_input("ズボンサイズ", value=st.session_state.order_data.get("pants_size", ""), placeholder="例: L", key="p_size", label_visibility="collapsed")

    col7, col8, col9 = st.columns([2, 1, 1])
    with col7: st.write(f"靴下 (¥{P_SOCKS:,})")
    with col8: socks_qty = st.selectbox("足数", options=list(range(11)), index=st.session_state.order_data.get("socks", 0), key="so_qty", label_visibility="collapsed")
    with col9: socks_size = st.text_input("靴下サイズ", value=st.session_state.order_data.get("socks_size", ""), placeholder="例: 24-26", key="so_size", label_visibility="collapsed")

    st.divider()
    
    total_price = (shirt_qty * P_SHIRT) + (pants_qty * P_PANTS) + (socks_qty * P_SOCKS)
    st.metric(label="合計金額", value=f"{total_price:,}円")

    if st.button("確認画面へ進む", use_container_width=True):
        if name and address and total_price > 0:
            # 入力情報をセッションに保存
            st.session_state.order_data = {
                "name": name,
                "phone": phone,
                "email": email,
                "zipcode": zipcode.replace("-", ""),
                "address": address,
                "shirt": shirt_qty,
                "shirt_size": shirt_size,
                "pants": pants_qty,
                "pants_size": pants_size,
                "socks": socks_qty,
                "socks_size": socks_size,
                "total_price": total_price
            }
            st.session_state.phase = "confirm"
            st.rerun()
        else:
            st.error("「お名前」「住所」を入力し、商品を1つ以上選択してください。")
