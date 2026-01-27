import re
import requests
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ===============================
# --- 画面設定 ---
# ===============================
st.set_page_config(page_title="注文登録", layout="wide")

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
# --- セッションステート初期化 ---
# ===============================
if "phase" not in st.session_state:
    st.session_state.phase = "login"
if "order_data" not in st.session_state:
    st.session_state.order_data = {}
if "order_id" not in st.session_state:
    st.session_state.order_id = None
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
# 郵便番号/住所の一時保持（確認や修正で戻ったときに復元）
if "zipcode_input" not in st.session_state:
    st.session_state.zipcode_input = st.session_state.order_data.get("zipcode", "")
if "address_input" not in st.session_state:
    st.session_state.address_input = st.session_state.order_data.get("address", "")

# ===============================
# --- 商品情報 ---
# ===============================
products = {
    "shirt": {"label": "シャツ", "price": 2000},
    "pants": {"label": "ズボン", "price": 3000},
    "socks": {"label": "靴下", "price": 500},
}

# ===============================
# --- CSS ---
# ===============================
st.markdown("""
<style>
/* 入力系の軽い縮小（PC共通） */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] {
  height: 32px; font-size: 13px;
}
.w-xs input, .w-xs div[data-baseweb="select"] { width: 60px !important; }
.w-s  input, .w-s  div[data-baseweb="select"] { width: 90px !important; }
.w-m  input, .w-m  div[data-baseweb="select"] { width: 160px !important; }
.w-l  input, .w-l  div[data-baseweb="select"] { width: 260px !important; }
.w-xl input { width: 100% !important; }

.header { font-weight: 600; font-size: 14px; color: #555; }
.total-box { background: #f5f7fa; padding: 10px; border-radius: 8px; text-align: right; font-size: 20px; font-weight: bold; }

/* スマホで少しコンパクトに */
@media (max-width: 480px) {
  div.stTextInput input { max-width: 180px; font-size: 13px; height: 30px; padding: 4px 8px; }
  div[data-baseweb="select"] { max-width: 200px; min-height: 30px; font-size: 13px; }
  div.stButton > button { max-width: 140px; height: 30px; font-size: 13px; padding: 4px 8px; }
  .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
}
</style>
""", unsafe_allow_html=True)

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
    """商品ごとの入力行（左ラベル／右入力／右余白）を1行ずつ構成。"""
    st.write(f"### {label}")

    if key == "pants":
        # 数量
        c_label, c_input, c_sp = st.columns([1, 1.2, 6])
        with c_label: st.markdown("数量")
        with c_input:
            qty = st.selectbox("", list(range(0, 11)), key=f"{key}_qty", label_visibility="collapsed")

        # ウエスト
        c_label, c_input, c_sp = st.columns([1, 1.2, 6])
        with c_label: st.markdown("ウエスト")
        with c_input:
            waist = st.selectbox(
                "", list(range(61, 111, 3)),
                index=None, placeholder="— 選択してください —",
                key=f"{key}_waist", label_visibility="collapsed"
            )

        # 丈
        c_label, c_input, c_sp = st.columns([1, 1.2, 6])
        with c_label: st.markdown("丈")
        with c_input:
            length = st.text_input("", key=f"{key}_length", placeholder="95", label_visibility="collapsed")

        # 備考
        c_label, c_input, c_sp = st.columns([1, 3, 4.2])
        with c_label: st.markdown("備考")
        with c_input:
            memo = st.text_input("", key=f"{key}_memo", placeholder="任意", label_visibility="collapsed")

        return {"qty": qty, "waist": waist, "length": length, "memo": memo}

    else:
        # シャツ・靴下
        # 数量
        c_label, c_input, c_sp = st.columns([1, 1.2, 6])
        with c_label: st.markdown("数量")
        with c_input:
            qty = st.selectbox("", list(range(0, 11)), key=f"{key}_qty", label_visibility="collapsed")

        # サイズ
        c_label, c_input, c_sp = st.columns([1, 1.8, 5.4])
        with c_label: st.markdown("サイズ")
        with c_input:
            if key == "shirt":
                size = st.selectbox(
                    "", ["S", "M", "L", "XL"],
                    index=None, placeholder="— 選択してください —",
                    key=f"{key}_size", label_visibility="collapsed"
                )
            else:  # socks
                size = st.text_input("", key=f"{key}_size", placeholder="25-27", label_visibility="collapsed")

        # 備考
        c_label, c_input, c_sp = st.columns([1, 3, 4.2])
        with c_label: st.markdown("備考")
        with c_input:
            memo = st.text_input("", key=f"{key}_memo", placeholder="任意", label_visibility="collapsed")

        return {"qty": qty, "size": size or "", "memo": memo}

# ===============================
# --- 入力画面 ---
# ===============================
if st.session_state.phase == "input":
    st.title("注文登録")

    # --- お客様情報 ---
    st.write("### 1. お客様情報")

    name = st.text_input("お名前（必須）", value=st.session_state.order_data.get("name", ""))

    # --- 郵便番号 + 住所検索（スマホでも100%横並び） ---
    # 直前の値をHTMLのvalueに表示（7桁までに整形）
    current_zip = re.sub(r"[^0-9]", "", st.session_state.get("zipcode_input", ""))[:7]

    components.html(f"""
<style>
  .zip-row {{
    display: flex; align-items: center; gap: 8px; width: 100%;
  }}
  .zip-row label {{ min-width: 72px; }}
  .zip-row input[type="text"] {{
    flex: 0 0 auto; max-width: 220px; padding: 8px; font-size: 16px;
  }}
  .zip-row button {{
    flex: 0 0 auto; padding: 8px 12px; font-size: 16px; white-space: nowrap;
  }}
  @media (max-width: 480px) {{
    .zip-row input[type="text"] {{ max-width: 160px; font-size: 15px; padding: 6px 8px; }}
    .zip-row button {{ font-size: 15px; padding: 6px 10px; }}
  }}
</style>
<form class="zip-row" method="get" action="">
  <label for="zip">郵便番号</label>
  <input id="zip" name="zip" type="text" inputmode="numeric" pattern="[0-9]*"
         placeholder="6008001" maxlength="7" value="{current_zip}">
  <button type="submit">住所検索</button>
</form>
""", height=70)

    # --- クエリパラメータから zip を取得（新API優先、旧APIfallback） ---
    try:
        # Streamlit 1.30+
        query_params = st.query_params
        zip_param = query_params.get("zip", None)
    except Exception:
        # 旧API
        query_params = st.experimental_get_query_params()
        zip_list = query_params.get("zip", [])
        zip_param = zip_list[0] if zip_list else None

    # --- zip が来ていれば検証→検索→住所反映 ---
    if zip_param:
        clean_zip = re.sub(r"[^0-9]", "", zip_param)
        st.session_state.zipcode_input = clean_zip  # 入力保持
        if re.fullmatch(r"\d{7}", clean_zip):
            try:
                res = requests.get(
                    f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={clean_zip}",
                    timeout=5
                ).json()
                if res.get("results"):
                    r = res["results"][0]
                    st.session_state.address_input = f"{r['address1']}{r['address2']}{r['address3']}"
                    st.success("住所を取得しました。下の住所欄をご確認ください。")
                else:
                    st.info("該当する住所が見つかりませんでした。郵便番号をご確認ください。")
            except Exception:
                st.error("住所検索に失敗しました。時間をおいて再度お試しください。")
        else:
            st.warning("郵便番号は7桁の数字で入力してください（例：6008001）。")

        # URLの ?zip= をクリアしてクリーンに戻す（新APIのみ）
        try:
            st.query_params.clear()
            st.rerun()
        except Exception:
            # 旧API環境ではURLクリアはスキップ
            pass

    # --- 住所（検索結果があれば初期値に反映） ---
    address = st.text_input(
        "住所（必須）",
        value=st.session_state.get("address_input", st.session_state.order_data.get("address", "")),
        placeholder="例：京都府京都市下京区四条通寺町東入2丁目御旅町"
    )

    phone = st.text_input("電話番号（任意）", value=st.session_state.order_data.get("phone", ""), placeholder="例：0751234567")
    email = st.text_input("メールアドレス（任意）", value=st.session_state.order_data.get("email", ""), placeholder="例：taro@example.com")

    st.divider()
    st.write("### 2. 商品選択")

    # --- 商品ごとにフォーム生成 ---
    order_data = {}
    for key, info in products.items():
        order_data[key] = product_row(info["label"], key)

    # --- 合計金額計算 ---
    total_price = sum(order_data[key]["qty"] * products[key]["price"] for key in products)
    st.markdown(f"<div class='total-box'>合計金額：{total_price:,} 円</div>", unsafe_allow_html=True)

    # --- 次へ（バリデーション含む） ---
    if st.button("確認画面へ進む", type="primary", use_container_width=True):
        zip_for_save = st.session_state.get("zipcode_input", "")
        is_zip_valid = bool(re.fullmatch(r"\d{7}", zip_for_save))
        if not name or not is_zip_valid or not address or total_price == 0:
            if not name:
                st.error("お名前（必須）を入力してください。")
            if not is_zip_valid:
                st.error("郵便番号（必須）は7桁の数字で入力し、『住所検索』を押してください（例：6008001）。")
            if not address:
                st.error("住所（必須）を入力してください。")
            if total_price == 0:
                st.error("商品数量を入力してください。")
        else:
            st.session_state.order_data = {
                "name": name,
                "zipcode": zip_for_save,
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
                    st.write(f"{info['label']}: {item['qty']}点 (ウエスト: {item['waist']}, 丈: {item['length']}){memo}")
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
            st.session_state["zipcode_input"] = data["zipcode"]

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
                **({"pants_waist": data["pants"]["waist"], "pants_length": data["pants"]["length"]} if "pants" in data else {}),
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
