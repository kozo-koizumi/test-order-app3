import streamlit as st
import requests
from supabase import create_client, Client

# --- Supabase設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

P_SHIRT, P_PANTS, P_SOCKS = 2000, 3000, 500

st.set_page_config(page_title="注文登録", layout="wide")

# ==================================================
# CSS（見た目のみ調整）
# ==================================================
st.markdown("""
<style>

/* 入力欄共通サイズ */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] {
    height: 32px;
    font-size: 13px;
}

/* 横幅プリセット */
.w-xs input, .w-xs div[data-baseweb="select"] { width: 60px !important; }
.w-s  input, .w-s  div[data-baseweb="select"] { width: 90px !important; }
.w-m  input, .w-m  div[data-baseweb="select"] { width: 160px !important; }
.w-l  input, .w-l  div[data-baseweb="select"] { width: 260px !important; }
.w-xl input { width: 100% !important; }

/* 見出し */
.header {
    font-weight: 600;
    font-size: 14px;
    color: #555;
}

/* 合計金額 */
.total-box {
    background: #f5f7fa;
    padding: 10px;
    border-radius: 8px;
    text-align: right;
    font-size: 20px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# session_state
# ==================================================
if "phase" not in st.session_state:
    st.session_state.phase = "input"
if "order_data" not in st.session_state:
    st.session_state.order_data = {}
if "order_id" not in st.session_state:
    st.session_state.order_id = None

# ==================================================
# 完了画面
# ==================================================
if st.session_state.phase == "complete":
    st.title("注文完了")
    st.write("ご注文ありがとうございました。")
    st.write(f"受付番号：{st.session_state.order_id}")
    st.write("受付番号をお控えください。")
    # 終了メッセージのみ 
    st.write("この画面を閉じて終了してください。")
    #if st.button("新しい注文を登録する"):
    #    st.session_state.phase = "input"
    #    st.session_state.order_data = {}
    #    st.session_state.order_id = None
    #    st.rerun()

# ==================================================
# 確認画面
# ==================================================
elif st.session_state.phase == "confirm":
    data = st.session_state.order_data

    st.title("注文内容の確認")

    col_info, col_order = st.columns(2)

    with col_info:
        st.write("【お客様情報】")
        st.write(f"お名前: {data['name']}")
        st.write(f"郵便番号: {data['zipcode']}")
        st.write(f"住所: {data['address']}")
        st.write(f"電話番号: {data['phone'] if data['phone'] else '未入力'}")
        st.write(f"メール: {data['email'] if data['email'] else '未入力'}")

    with col_order:
        st.write("【注文商品】")
        for item, label in [("shirt", "シャツ"), ("pants", "ズボン"), ("socks", "靴下")]:
            if data[item] > 0:
                memo = f" / 備考: {data[item+'_memo']}" if data[item+'_memo'] else ""
                st.write(
                    f"{label}: {data[item]}点 ({data[item+'_size']}){memo}"
                )
        st.write(f"合計金額: {data['total_price']:,}円")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("修正する", use_container_width=True):
            st.session_state.phase = "input"
            st.rerun()

    with c2:
        if st.button("確定する", type="primary", use_container_width=True):
            res = supabase.table("orders").insert(data).execute()
            if res.data:
                st.session_state.order_id = res.data[0]["id"]
            st.session_state.phase = "complete"
            st.rerun()

# ==================================================
# 入力画面
# ==================================================
else:
    st.title("注文登録")

    # ---------- お客様情報 ----------
    st.write("### 1. お客様情報")

    st.markdown("<div class='w-m'>", unsafe_allow_html=True)
    name = st.text_input(
        "お名前（必須）",
        value=st.session_state.order_data.get("name", "")
    )
    st.markdown("</div>", unsafe_allow_html=True)

    z1, z2 = st.columns([1, 4])

    with z1:
        st.markdown("<div class='w-s'>", unsafe_allow_html=True)
        zipcode = st.text_input(
            "郵便番号",
            value=st.session_state.order_data.get("zipcode", ""),
            placeholder="1234567",
            max_chars=7
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with z2:
        st.write("")
        if st.button("住所検索"):
            clean_zip = zipcode.replace("-", "").replace(" ", "")
            res = requests.get(
                f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={clean_zip}"
            ).json()
            if res.get("results"):
                r = res["results"][0]
                st.session_state.address_input = (
                    r["address1"] + r["address2"] + r["address3"]
                )

    st.markdown("<div class='w-xl'>", unsafe_allow_html=True)
    address = st.text_input(
        "住所（必須）",
        value=st.session_state.get(
            "address_input",
            st.session_state.order_data.get("address", "")
        )
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='w-m'>", unsafe_allow_html=True)
    phone = st.text_input(
        "電話番号（任意）",
        value=st.session_state.order_data.get("phone", "")
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='w-l'>", unsafe_allow_html=True)
    email = st.text_input(
        "メールアドレス（任意）",
        value=st.session_state.order_data.get("email", "")
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ---------- 商品 ----------
    st.write("### 2. 商品選択")

    h = st.columns([1.2, 0.7, 0.8, 4])
    h[0].markdown("<div class='header'>商品</div>", unsafe_allow_html=True)
    h[1].markdown("<div class='header'>数量</div>", unsafe_allow_html=True)
    h[2].markdown("<div class='header'>サイズ</div>", unsafe_allow_html=True)
    h[3].markdown("<div class='header'>備考</div>", unsafe_allow_html=True)

    def product_row(label, price, key_prefix):
        cols = st.columns([1.2, 0.7, 0.8, 4])

        with cols[0]:
            st.write(label)

        with cols[1]:
            st.markdown("<div class='w-xs'>", unsafe_allow_html=True)
            qty = st.selectbox(
                f"q_{key_prefix}",
                options=list(range(11)),
                index=st.session_state.order_data.get(key_prefix, 0),
                key=f"{key_prefix}_q",
                label_visibility="collapsed"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with cols[2]:
            st.markdown("<div class='w-xs'>", unsafe_allow_html=True)
            size = st.text_input(
                f"s_{key_prefix}",
                value=st.session_state.order_data.get(f"{key_prefix}_size", ""),
                key=f"{key_prefix}_s",
                placeholder="M",
                label_visibility="collapsed"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with cols[3]:
            st.markdown("<div class='w-xl'>", unsafe_allow_html=True)
            memo = st.text_input(
                f"m_{key_prefix}",
                value=st.session_state.order_data.get(f"{key_prefix}_memo", ""),
                key=f"{key_prefix}_m",
                placeholder="備考を入力",
                label_visibility="collapsed"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        return qty, size, memo

    s_qty, s_size, s_memo = product_row("シャツ", P_SHIRT, "shirt")
    p_qty, p_size, p_memo = product_row("ズボン", P_PANTS, "pants")
    so_qty, so_size, so_memo = product_row("靴下", P_SOCKS, "socks")

    total_price = (
        s_qty * P_SHIRT +
        p_qty * P_PANTS +
        so_qty * P_SOCKS
    )

    st.markdown(
        f"<div class='total-box'>合計金額：{total_price:,} 円</div>",
        unsafe_allow_html=True
    )

    if st.button("確認画面へ進む", use_container_width=True, type="primary"):
        if name and address and total_price > 0:
            st.session_state.order_data = {
                "name": name,
                "zipcode": zipcode,
                "address": address,
                "phone": phone,
                "email": email,
                "shirt": s_qty,
                "shirt_size": s_size,
                "shirt_memo": s_memo,
                "pants": p_qty,
                "pants_size": p_size,
                "pants_memo": p_memo,
                "socks": so_qty,
                "socks_size": so_size,
                "socks_memo": so_memo,
                "total_price": total_price
            }
            st.session_state.phase = "confirm"
            st.rerun()
