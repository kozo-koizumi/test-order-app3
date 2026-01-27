import streamlit as st
import requests
from supabase import create_client, Client

# ===============================
# --- Supabase設定 ---
# ===============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===============================
# --- 固定ユーザー認証 ---
# ===============================
FIXED_USER_ID = st.secrets["USER_ID"]
FIXED_PASSWORD = st.secrets["PASSWORD"]

# ===============================
# --- 商品情報 ---
# ===============================
products = {
    "shirt": {"label": "シャツ", "price": 2000},
    "pants": {"label": "ズボン", "price": 3000},
    "socks": {"label": "靴下", "price": 500},
}

st.set_page_config(page_title="注文登録", layout="wide")

# ===============================
# --- CSS ---
# ===============================
st.markdown("""
<style>
.stTextInput input,
.stSelectbox div[data-baseweb="select"] { height: 32px; font-size: 13px; }
.w-xs input, .w-xs div[data-baseweb="select"] { width: 60px !important; }
.w-s  input, .w-s  div[data-baseweb="select"] { width: 90px !important; }
.w-m  input, .w-m  div[data-baseweb="select"] { width: 160px !important; }
.w-l  input, .w-l  div[data-baseweb="select"] { width: 260px !important; }
.w-xl input { width: 100% !important; }
.header { font-weight: 600; font-size: 14px; color: #555; }
.total-box { background: #f5f7fa; padding: 10px; border-radius: 8px; text-align: right; font-size: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ===============================
# --- セッションステート初期化 ---
# ===============================
if "phase" not in st.session_state: st.session_state.phase = "login"
if "order_data" not in st.session_state: st.session_state.order_data = {}
if "order_id" not in st.session_state: st.session_state.order_id = None
if "user_logged_in" not in st.session_state: st.session_state.user_logged_in = False

# ===============================
# --- ログイン画面 ---
# ===============================
if not st.session_state.user_logged_in:
    st.title("ログイン")
    user_id_input = st.text_input("ユーザーID")
    password_input = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if user_id_input == FIXED_USER_ID and password_input == FIXED_PASSWORD:
            st.session_state.user_logged_in = True
            st.session_state.phase = "input"
            st.success("ログイン成功")
            st.rerun()
        else:
            st.error("ログイン失敗")
    st.stop()

# ===============================
# --- 入力画面用関数 ---
# ===============================
def product_row(label, key):
    """商品ごとの入力行を作成"""
    st.write(f"### {label}")  # 商品名を表示

    if key == "pants":
        # ズボン: 数量・ウェスト・丈・備考
        c = st.columns([1,1,1,2])
        with c[0]: st.write("数量")
        with c[1]: st.write("ウェスト")
        with c[2]: st.write("丈")
        with c[3]: st.write("備考")
        # 入力
        with c[0]:
            qty = st.selectbox("", range(11), key=f"{key}_qty")
        with c[1]:
            waist = st.selectbox("", list(range(61,111,3)), key=f"{key}_waist", index=None)
        with c[2]:
            length = st.text_input("", key=f"{key}_length", placeholder="丈を入力")
        with c[3]:
            memo = st.text_input("", key=f"{key}_memo", placeholder="備考を入力")
        return {"qty": qty, "waist": waist, "length": length, "memo": memo}
    
    else:
        # シャツ・靴下: 数量・サイズ・備考
        c = st.columns([1,1,2])
        with c[0]: st.write("数量")
        with c[1]: st.write("サイズ")
        with c[2]: st.write("備考")
        # 入力
        with c[0]:
            qty = st.selectbox("", range(11), key=f"{key}_qty")
        with c[1]:
            if key == "shirt":
                size = st.selectbox("", ["S","M","L","XL"], index=None, key=f"{key}_size", format_func=lambda x: "" if x is None else x)
            elif key == "socks":
                size = st.text_input("", key=f"{key}_size", placeholder="サイズを入力")
            else:
                size = ""
        with c[2]:
            memo = st.text_input("", key=f"{key}_memo", placeholder="備考を入力")
        return {"qty": qty, "size": size, "memo": memo}

# ===============================
# --- 入力画面 ---
# ===============================
if st.session_state.phase == "input":
    st.title("注文登録")

    if st.button("ログアウト"):
        st.session_state.clear()
        st.rerun()

    # --- お客様情報 ---
    st.write("### 1. お客様情報")
    name = st.text_input("お名前（必須）", value=st.session_state.order_data.get("name", ""))
    zipcode = st.text_input("郵便番号(必須)  ハイフンなしで入力", value=st.session_state.order_data.get("zipcode",""), max_chars=7)

    if st.button("住所検索"):
        clean_zip = zipcode.replace("-", "").replace(" ", "")
        res = requests.get(f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={clean_zip}").json()
        if res.get("results"):
            r = res["results"][0]
            st.session_state.address_input = r["address1"] + r["address2"] + r["address3"]

    address = st.text_input(
        "住所（必須）",
        value=st.session_state.get("address_input", st.session_state.order_data.get("address",""))
    )
    phone = st.text_input("電話番号（任意）", value=st.session_state.order_data.get("phone",""))
    email = st.text_input("メールアドレス（任意）", value=st.session_state.order_data.get("email",""))

    st.divider()
    st.write("### 2. 商品選択")

    # --- 商品ごとにフォーム生成 ---
    order_data = {}
    for key, info in products.items():
        order_data[key] = product_row(info["label"], key)

    # --- 合計金額計算 ---
    total_price = sum(order_data[key]["qty"] * products[key]["price"] for key in products)

    st.markdown(f"<div class='total-box'>合計金額：{total_price:,} 円</div>", unsafe_allow_html=True)

    if st.button("確認画面へ進む", type="primary", use_container_width=True):
        if not name or not address or total_price == 0:
            st.error("必須項目を入力してください")
        else:
            st.session_state.order_data = {
                "name": name,
                "zipcode": zipcode,
                "address": address,
                "phone": phone,
                "email": email,
                **order_data,
                "total_price": total_price
            }
            st.session_state.phase = "confirm"
            st.rerun()

# ===============================
# --- 確認画面 ---
# ===============================
elif st.session_state.phase == "confirm":
    data = st.session_state.order_data
    st.title("注文内容の確認")

    col_info, col_order = st.columns(2)
    with col_info:
        st.write("【お客様情報】")
        st.write(f"お名前: {data['name']}")
        st.write(f"郵便番号: {data['zipcode']}")
        st.write(f"住所: {data['address']}")
        st.write(f"電話番号: {data.get('phone','未入力')}")
        st.write(f"メール: {data.get('email','未入力')}")

    with col_order:
        st.write("【注文商品】")
        for key, info in products.items():
            item = data[key]
            if item["qty"] > 0:
                if key == "pants":
                    memo = f" / 備考: {item['memo']}" if item["memo"] else ""
                    st.write(f"{info['label']}: {item['qty']}点 (ウェスト: {item['waist']}, 丈: {item['length']}){memo}")
                else:
                    memo = f" / 備考: {item['memo']}" if item["memo"] else ""
                    st.write(f"{info['label']}: {item['qty']}点 ({item['size']}){memo}")
        st.write(f"合計金額: {data['total_price']:,}円")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
       if st.button("修正する", use_container_width=True):
        data = st.session_state.order_data

        # --- 商品入力値を session_state に戻す ---
        for key in products:
            st.session_state[f"{key}_qty"] = data[key]["qty"]
            st.session_state[f"{key}_memo"] = data[key]["memo"]

            if key == "pants":
                st.session_state["pants_waist"] = data["pants"]["waist"]
                st.session_state["pants_length"] = data["pants"]["length"]
            else:
                st.session_state[f"{key}_size"] = data[key]["size"]

        # --- 顧客情報 ---
        st.session_state["address_input"] = data["address"]

        st.session_state.phase = "input"
        st.rerun()
    with c2:
        if st.button("確定する", type="primary", use_container_width=True):
            insert_data = {
                "name": data["name"],
                "zipcode": data["zipcode"],
                "address": data["address"],
                "phone": data["phone"],
                "email": data["email"],
                **{f"{key}": data[key]["qty"] for key in products},
                **{f"{key}_memo": data[key]["memo"] for key in products},
                **({f"pants_waist": data['pants']['waist'], f"pants_length": data['pants']['length']} if 'pants' in data else {}),
                **({f"{key}_size": data[key]["size"] for key in products if key != "pants"})
            }
            res = supabase.table("orders").insert(insert_data).execute()
            if res.data:
                st.session_state.order_id = res.data[0]["id"]
            st.session_state.phase = "complete"
            st.rerun()

# ===============================
# --- 完了画面 ---
# ===============================
elif st.session_state.phase == "complete":
    st.title("注文完了")
    st.write("ご注文ありがとうございました。")
    st.write(f"受付番号：{st.session_state.order_id}")
    st.write("受付番号をお控えください。")
    st.session_state.pop("address_input", None)

    if st.button("ログアウト"):
        st.session_state.clear()
        st.rerun()
