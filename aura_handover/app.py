# =====================================================================================
#  AURA DSS – Dashboard Streamlit (4 tab). UI CHỈ GỌI LÕI: model.FPDModel + llm.LLM/PrivacyGuard.
#  Chạy:  streamlit run app.py        (Colab: xem HUONG_DAN_CHAY.md)
#  Nếu không nạp được lõi/dữ liệu -> tự chuyển DEMO_MODE (dữ liệu giả lập cùng cấu trúc) để xem giao diện.
# =====================================================================================
import os, json, time, sqlite3, traceback
import numpy as np, pandas as pd, streamlit as st
import plotly.graph_objects as go, plotly.express as px

# ------------------------------------------------------------------ cấu hình
BASE = os.environ.get("AURA_BASE", "/content/drive/MyDrive/Colab Notebooks/")
MODEL_DIR, DB_PATH, HINH_DIR = BASE + "fpd_model_v1", BASE + "aura_bnpl.db", BASE + "hinh/"
FORCE_DEMO = os.environ.get("AURA_DEMO", "0") == "1"
SO_TINH = {"auc_thick": 0.7900, "auc_thin": 0.7704, "no_xau_backtest": 2.86, "no_xau_nen": 8.07, "p99_ms": 7.6}
LABELS = ["1. Low Risk (An toàn - Cấp hạn mức tối đa)", "2. Medium Risk (Thăm dò - Hạn mức kiểm soát)",
          "3. High Risk (Nguy cơ - Từ chối / Chuyển AI Coach)"]
SYSTEM_PROMPT = ("Bạn là trợ lý thẩm định tín dụng BNPL của ví Aura. Chỉ dùng số liệu có trong FACTS; nếu thiếu, ghi "
                 "'(không có số liệu)'. Trả lời tiếng Việt, tối đa 150 từ, đúng 3 phần: Kết luận – Lý do chính – Khuyến nghị. "
                 "Tuyệt đối không tự thay đổi tầng rủi ro, xác suất hay quyết định đã cho.")

st.set_page_config(page_title="Aura DSS", page_icon="💠", layout="wide")

# ------------------------------------------------------------------ tiện ích hiển thị
def vnd(x):  return f"{float(x):,.0f}".replace(",", ".") + " ₫"
def pct(x, d=2): return f"{float(x)*100:.{d}f}".replace(".", ",") + " %"
def num(x, d=2): return f"{float(x):.{d}f}".replace(".", ",")
def tier_color(tier): return {"1": "#2e7d32", "2": "#f9a825", "3": "#c62828"}.get(str(tier)[:1], "#546e7a")
def tier_short(tier): return {"1": "LOW", "2": "MEDIUM", "3": "HIGH"}.get(str(tier)[:1], "?")
def badge(text, color):
    st.markdown(f"<span style='background:{color};color:white;padding:4px 12px;border-radius:12px;font-weight:600'>{text}</span>",
                unsafe_allow_html=True)
def model_label(m): return "Thick-file (188 đặc trưng, có lịch sử)" if m == "thick" else "Thin-file (82 đặc trưng, khách mới)"

from demo_core import DemoModel, DemoLLM, DemoGuard, demo_kiem_tra_so

# ------------------------------------------------------------------ nạp lõi
@st.cache_resource(show_spinner="Đang nạp mô hình…")
def load_core():
    if FORCE_DEMO: return DemoModel(), DemoLLM(), DemoGuard(), demo_kiem_tra_so, True, "AURA_DEMO=1"
    try:
        import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from model import FPDModel
        from llm import LLM, PrivacyGuard, kiem_tra_so
        m = FPDModel(model_dir=MODEL_DIR, db_path=DB_PATH)
        try: llm = LLM()
        except Exception as e: llm = DemoLLM(); st.session_state["llm_err"] = str(e)
        return m, llm, PrivacyGuard(), kiem_tra_so, False, ""
    except Exception as e:
        return DemoModel(), DemoLLM(), DemoGuard(), demo_kiem_tra_so, True, f"{type(e).__name__}: {e}"

M, LLM_, GUARD, KIEM_TRA_SO, DEMO, DEMO_REASON = load_core()

def sql(q, params=()):
    if DEMO: return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as c: return pd.read_sql(q, c, params=params)

def goi_llm(facts: dict, fallback_text: str):
    """Gọi LLM với guardrail; lỗi -> bản mẫu ngoại tuyến. Trả về (text, model_name, canh_bao, offline)."""
    fs = json.dumps(facts, ensure_ascii=False, default=str)
    try:
        text, model_name = LLM_.ask(SYSTEM_PROMPT, "FACTS:\n" + fs)
        return text, model_name, KIEM_TRA_SO(text, fs), False
    except Exception as e:
        return fallback_text, f"ngoại tuyến ({type(e).__name__})", [], True

def ban_mau(score, ex, han_muc):
    ly_do = "; ".join(f"{t['ten']} ({t['mo_ta']})" for t in ex["tang_rui_ro"][:3]) or "(không có số liệu)"
    return (f"**Kết luận:** P_FPD = {pct(score['p'])} → tầng {tier_short(score['tier'])}; hạn mức gợi ý {vnd(han_muc)}.\n\n"
            f"**Lý do chính:** {ly_do}.\n\n**Khuyến nghị:** {ex['goi_y'][0] if ex['goi_y'] else '(không có số liệu)'}.")

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("## 💠 AURA DSS")
    st.caption("Hệ hỗ trợ ra quyết định tín dụng BNPL")
    st.markdown("**3 mô hình**\n- Thick-file FPD (LightGBM)\n- Thin-file FPD (LightGBM)\n- MILP phân bổ vốn (PuLP/CBC)")
    st.markdown(f"Ngưỡng tầng: Low < {num(M.low*100,1)} % ≤ Medium < {num(M.high*100,1)} % ≤ High")
    if DEMO: st.warning("Chế độ DEMO – dữ liệu giả lập\n\n" + (DEMO_REASON or ""))
    else: st.success("Lõi thật: FPDModel + SQLite")
if DEMO: st.markdown("<div style='background:#fff3cd;border:1px solid #ffeeba;padding:8px 14px;border-radius:6px;color:#856404;font-weight:600'>DEMO – dữ liệu giả lập, không phải kết quả mô hình thật</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Tổng quan điều hành", "🔎 Thẩm định hồ sơ", "⚖️ Phân bổ vốn (MILP)", "📜 Nhật ký & Đạo đức"])

# ================================================================== TAB 1
def render_tab_1():
    try: ps = M.portfolio_summary()
    except Exception as e: st.error(f"Không đọc được tổng quan danh mục: {e}"); return
    tiers, log = ps["tiers"], ps["decision_log"]
    p99 = ps.get("latency_ms", {}).get("feature_store_p99", SO_TINH["p99_ms"])
    c = st.columns(6)
    c[0].metric("AUC thick-file", num(SO_TINH["auc_thick"], 3)); c[1].metric("AUC thin-file", num(SO_TINH["auc_thin"], 3))
    c[2].metric("Nợ xấu backtest", num(SO_TINH["no_xau_backtest"]) + " %", f"nền {num(SO_TINH['no_xau_nen'])} %", delta_color="inverse")
    c[3].metric("Độ trễ P99", num(p99, 1) + " ms", "mục tiêu < 50 ms")
    c[4].metric("Khách đã chấm", f"{int(tiers.so_khach.sum()):,}".replace(",", "."))
    c[5].metric("Quyết định đã ghi", f"{int(log.so_don.sum()) if len(log) else 0:,}".replace(",", "."))
    a, b = st.columns([3, 2])
    with a:
        fig = go.Figure()
        fig.add_bar(name="P dự đoán TB", x=[tier_short(t) for t in tiers.risk_tier], y=tiers.p_tb * 100, marker_color="#1565c0")
        fig.add_bar(name="Nợ xấu thật", x=[tier_short(t) for t in tiers.risk_tier], y=tiers.no_xau_that * 100, marker_color="#ef6c00")
        fig.update_layout(barmode="group", title="Hiệu chuẩn theo tầng rủi ro (%)", height=360, yaxis_title="%")
        st.plotly_chart(fig, use_container_width=True)
    with b:
        fig = px.pie(tiers, names=[tier_short(t) for t in tiers.risk_tier], values="so_khach", hole=.55, title="Phân bố khách theo tầng",
                     color=[tier_short(t) for t in tiers.risk_tier], color_discrete_map={"LOW": "#2e7d32", "MEDIUM": "#f9a825", "HIGH": "#c62828"})
        fig.update_layout(height=360); st.plotly_chart(fig, use_container_width=True)
    if os.path.exists(HINH_DIR + "flow_aura.png"): st.image(HINH_DIR + "flow_aura.png", caption="Kiến trúc & luồng dữ liệu Aura", use_container_width=True)
    st.subheader("Các lô quyết định gần nhất")
    if len(log):
        show = log.copy(); show["von"] = show["von"].map(vnd); show["p_tb"] = show["p_tb"].map(pct)
        show["decision"] = show["decision"].map({1: "Duyệt", 0: "Từ chối"})
        st.dataframe(show.head(20), use_container_width=True, hide_index=True)
    else: st.info("(không có số liệu)")

# ================================================================== TAB 2
def gauge(p):
    fig = go.Figure(go.Indicator(mode="gauge+number", value=p * 100, number={"suffix": " %", "valueformat": ".2f"},
        title={"text": "Xác suất bùng nợ kỳ đầu (P_FPD)"},
        gauge={"axis": {"range": [0, max(30, p * 100 * 1.2)]}, "bar": {"color": "#263238"},
               "steps": [{"range": [0, M.low * 100], "color": "#c8e6c9"}, {"range": [M.low * 100, M.high * 100], "color": "#fff59d"},
                         {"range": [M.high * 100, 100], "color": "#ffcdd2"}]}))
    fig.update_layout(height=280, margin=dict(t=60, b=10)); return fig

def hien_ket_qua(score, ex, khach=None, income_year=None):
    m_used = score.get("model_used") or ex.get("model_used", "thick")
    han_muc = score.get("han_muc_goi_y", None)
    if han_muc is None:
        try: han_muc = M.han_muc(score["p"], m_used, income_year)
        except Exception: han_muc = 0
    a, b = st.columns([2, 3])
    with a:
        st.plotly_chart(gauge(score["p"]), use_container_width=True)
        badge("Tầng " + tier_short(score["tier"]), tier_color(score["tier"])); st.write("")
        badge("Mô hình: " + model_label(m_used), "#1565c0"); st.write("")
        st.metric("Hạn mức gợi ý", vnd(han_muc))
        if khach: st.caption("Khách: " + " · ".join(f"{k}: {v}" for k, v in khach.items() if k in ("full_name", "phone_number")))
    with b:
        st.markdown("**Yếu tố làm tăng rủi ro (SHAP)**")
        if ex["tang_rui_ro"]:
            st.dataframe(pd.DataFrame(ex["tang_rui_ro"])[["ten", "mo_ta", "shap"]].rename(columns={"ten": "Yếu tố", "mo_ta": "Mức độ", "shap": "SHAP"}).style
                         .format({"SHAP": "{:+.3f}"}).map(lambda v: "color:#c62828;font-weight:600", subset=["SHAP"]), use_container_width=True, hide_index=True)
        else: st.caption("(không có số liệu)")
        st.markdown("**Yếu tố làm giảm rủi ro**")
        if ex["giam_rui_ro"]:
            st.dataframe(pd.DataFrame(ex["giam_rui_ro"])[["ten", "mo_ta", "shap"]].rename(columns={"ten": "Yếu tố", "mo_ta": "Mức độ", "shap": "SHAP"}).style
                         .format({"SHAP": "{:+.3f}"}).map(lambda v: "color:#2e7d32;font-weight:600", subset=["SHAP"]), use_container_width=True, hide_index=True)
        else: st.caption("(không có số liệu)")
        st.markdown("**Gợi ý xử lý:** " + " · ".join(ex.get("goi_y", [])))
    st.divider()
    if st.button("🤖 Giải thích bằng AI (Gemini)", key=f"llm_{score.get('customer_id','new')}"):
        with st.spinner("Đang hỏi Gemini…"):
            facts = {"score": {"p": round(score["p"], 4), "tier": score["tier"], "model_used": m_used, "han_muc": han_muc},
                     "explain": ex, "khach": khach or {}}
            text, model_name, canh_bao, offline = goi_llm(facts, ban_mau(score, ex, han_muc))
        if offline: st.warning("Chế độ ngoại tuyến – bản giải thích mẫu dựng từ SHAP/MILP (LLM không khả dụng).")
        st.markdown(text); st.caption(f"Model: {model_name}")
        for w in canh_bao: st.error("Guardrail: " + str(w))

def render_tab_2():
    mode = st.radio("Đối tượng", ["Khách hàng có sẵn trong CSDL", "Khách hàng mới (thin-file)"], horizontal=True)
    if mode.startswith("Khách hàng có sẵn"):
        cid = st.number_input("customer_id", value=243023, step=1, min_value=0)
        if st.button("Chấm điểm", type="primary"):
            try:
                score = M.score_customer(int(cid)); ex = M.explain(int(cid))
                pii = sql("SELECT full_name, phone_number, device_id, last_gps_location FROM DIM_CUSTOMER_PII WHERE customer_id=?", (int(cid),))
                khach = GUARD.sanitize(pii.iloc[0].to_dict()) if len(pii) else None
                st.session_state["kq2"] = (score, ex, khach, None)
            except KeyError as e: st.error(str(e)); st.session_state.pop("kq2", None)
            except Exception as e: st.error(f"Lỗi chấm điểm: {e}"); st.session_state.pop("kq2", None)
        if "kq2" in st.session_state: hien_ket_qua(*st.session_state["kq2"])
    else:
        cc = M.cat_categories
        with st.form("form_moi"):
            c1, c2, c3 = st.columns(3)
            loai = c1.selectbox("Loại hợp đồng", cc.get("NAME_CONTRACT_TYPE", ["Cash loans"]))
            thu_nhap = c1.number_input("Thu nhập (VNĐ/tháng)", 1_000_000, 500_000_000, 12_000_000, 500_000)
            tuoi = c1.slider("Tuổi", 18, 70, 32); nam_lam = c1.slider("Số năm làm việc", 0, 45, 4)
            vay = c2.number_input("Số tiền muốn vay (đv gốc)", 10_000, 5_000_000, 450_000, 10_000)
            tra_gop = c2.number_input("Trả góp mỗi kỳ (đv gốc)", 1_000, 300_000, 25_000, 1_000)
            gia = c2.number_input("Giá hàng hoá (đv gốc)", 10_000, 5_000_000, 400_000, 10_000)
            kv = c2.selectbox("Xếp hạng khu vực", [1, 2, 3], 1)
            e1 = c3.slider("EXT_SOURCE_1", 0.0, 1.0, 0.5, 0.01); k1 = c3.checkbox("Không có EXT_SOURCE_1", True)
            e2 = c3.slider("EXT_SOURCE_2", 0.0, 1.0, 0.55, 0.01); k2 = c3.checkbox("Không có EXT_SOURCE_2")
            e3 = c3.slider("EXT_SOURCE_3", 0.0, 1.0, 0.45, 0.01); k3 = c3.checkbox("Không có EXT_SOURCE_3")
            d1, d2, d3 = st.columns(3)
            hoc_van = d1.selectbox("Học vấn", cc.get("NAME_EDUCATION_TYPE", [])); hon_nhan = d1.selectbox("Hôn nhân", cc.get("NAME_FAMILY_STATUS", []))
            nha = d2.selectbox("Nhà ở", cc.get("NAME_HOUSING_TYPE", [])); nghe = d2.selectbox("Nghề nghiệp", cc.get("OCCUPATION_TYPE", []))
            to_chuc = d3.selectbox("Loại tổ chức", cc.get("ORGANIZATION_TYPE", []))
            so_con = d3.number_input("Số con", 0, 10, 0); tv = d3.number_input("Số thành viên gia đình", 1, 15, 2)
            xe = d1.radio("Sở hữu xe", ["N", "Y"], horizontal=True); bds = d2.radio("Sở hữu BĐS", ["N", "Y"], horizontal=True)
            ok = st.form_submit_button("Chấm điểm khách mới", type="primary")
        if ok:
            form = {"NAME_CONTRACT_TYPE": loai, "AMT_INCOME_TOTAL": thu_nhap * 12 / 1000, "AMT_CREDIT": vay, "AMT_ANNUITY": tra_gop,
                    "AMT_GOODS_PRICE": gia, "DAYS_BIRTH": -tuoi * 365, "DAYS_EMPLOYED": -nam_lam * 365,
                    "EXT_SOURCE_1": np.nan if k1 else e1, "EXT_SOURCE_2": np.nan if k2 else e2, "EXT_SOURCE_3": np.nan if k3 else e3,
                    "NAME_EDUCATION_TYPE": hoc_van, "NAME_FAMILY_STATUS": hon_nhan, "NAME_HOUSING_TYPE": nha, "OCCUPATION_TYPE": nghe,
                    "ORGANIZATION_TYPE": to_chuc, "REGION_RATING_CLIENT": kv, "CNT_CHILDREN": so_con, "CNT_FAM_MEMBERS": tv,
                    "FLAG_OWN_CAR": xe, "FLAG_OWN_REALTY": bds}
            try:
                score = M.score_new(form); ex = M.explain(form=form)
                st.session_state["kq2n"] = (score, ex, None, form["AMT_INCOME_TOTAL"])
            except Exception as e: st.error(f"Lỗi chấm điểm khách mới: {e}"); st.code(traceback.format_exc()); st.session_state.pop("kq2n", None)
        if "kq2n" in st.session_state: hien_ket_qua(*st.session_state["kq2n"])

# ================================================================== TAB 3
def render_tab_3():
    c0, c1 = st.columns([1, 3])
    with c0:
        quy = st.slider("Quỹ vốn (tỷ VNĐ)", 1.0, 3.0, 2.0, 0.1)
        tran = st.slider("Trần nợ xấu danh mục (%)", 2.0, 6.0, 4.0, 0.5)
        lgd = st.slider("LGD – tỷ lệ mất vốn khi nợ xấu", 0.4, 0.8, 0.6, 0.05)
        seed = st.number_input("Mã lô (seed)", 0, 9999, 42); n = st.selectbox("Số giao dịch/lô", [500, 1000, 2000], 1)
        run = st.button("▶ Chạy tối ưu (PuLP/CBC)", type="primary")
    if run:
        try:
            with st.spinner("Đang giải MILP…"):
                d, kq = M.optimize(liquidity=quy * 1e9, risk_ceiling=tran / 100, lgd=lgd, n=n, seed=int(seed))
            st.session_state["kq3"] = (d, kq, dict(quy=quy, tran=tran, lgd=lgd, seed=int(seed), n=n))
        except Exception as e: st.error(f"Lỗi solver: {e}"); st.code(traceback.format_exc())
    if "kq3" not in st.session_state:
        with c1: st.info("Chỉnh tham số bên trái và bấm **Chạy tối ưu**. Mặc định (2 tỷ, 4 %, LGD 0,6, lô 42) tái tạo kết quả báo cáo: 660/1.000 đơn, 43,04 triệu.")
        return
    d, kq, prm = st.session_state["kq3"]
    with c1:
        k = st.columns(5)
        k[0].metric("Trạng thái", kq["status"], f"{kq['solver']} · {kq['solve_s']*1000:.0f} ms")
        k[1].metric("Đơn duyệt", f"{kq['so_don_duyet']}/{kq['n']}", pct(kq["ty_le_duyet"]))
        k[2].metric("Vốn giải ngân", vnd(kq["von"]), f"{pct(kq['su_dung_von'])} quỹ")
        k[3].metric("Nợ xấu dự đoán", pct(kq["no_xau_du_doan"]), f"trần {num(prm['tran'],1)} %", delta_color="off")
        k[4].metric("Lợi nhuận kỳ vọng", vnd(kq["loi_nhuan_kv"]), f"MDR {vnd(kq['phi_mdr'])}")
        rb = kq["rang_buoc_cham"]; x, y = st.columns(2)
        with x: badge("Ràng buộc thanh khoản: " + ("CHẠM" if rb["thanh_khoan"] else "không chạm"), "#c62828" if rb["thanh_khoan"] else "#546e7a")
        with y: badge("Ràng buộc rủi ro: " + ("CHẠM" if rb["rui_ro"] else "không chạm"), "#c62828" if rb["rui_ro"] else "#546e7a")
        st.write("")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**Duyệt theo tầng rủi ro**")
            t = pd.DataFrame(kq["duyet_theo_tier"]).T.reset_index().rename(columns={"index": "Tầng", "so_don": "Số đơn", "ty_le_duyet": "Tỷ lệ duyệt"})
            t["Tầng"] = t["Tầng"].map(tier_short); t["Tỷ lệ duyệt"] = t["Tỷ lệ duyệt"].map(pct); st.dataframe(t, hide_index=True, use_container_width=True)
        with b:
            st.markdown("**Theo luồng mô hình**")
            t = pd.DataFrame(kq["theo_model"]).T.reset_index().rename(columns={"index": "Mô hình", "size": "Số đơn", "mean": "Tỷ lệ duyệt"})
            t["Tỷ lệ duyệt"] = t["Tỷ lệ duyệt"].map(pct); st.dataframe(t, hide_index=True, use_container_width=True)
        with c:
            vc = d[d.decision == 0]["ly_do"].value_counts().reset_index(); vc.columns = ["Lý do từ chối", "Số đơn"]
            st.plotly_chart(px.bar(vc, x="Số đơn", y="Lý do từ chối", orientation="h", height=220, title="Lý do từ chối").update_layout(margin=dict(t=40, b=10)), use_container_width=True)
    with st.expander("📈 Phân tích độ nhạy theo trần nợ xấu", expanded=False):
        if st.button("Chạy độ nhạy với tham số hiện tại"):
            try:
                with st.spinner("Đang giải 5 bài toán…"):
                    st.session_state["sens"] = M.sensitivity((0.02, 0.03, 0.04, 0.05, 0.06), liquidity=prm["quy"] * 1e9, lgd=prm["lgd"], n=prm["n"], seed=prm["seed"])
            except Exception as e: st.error(f"Lỗi độ nhạy: {e}")
        if "sens" in st.session_state:
            s = st.session_state["sens"]; xs = [f"{r*100:.0f}%" for r in s.tran_rui_ro]
            f1 = go.Figure(); f1.add_bar(name="Tỷ lệ duyệt (%)", x=xs, y=s.ty_le_duyet * 100, marker_color="#90caf9")
            f1.add_bar(name="Vốn sử dụng (%)", x=xs, y=s.su_dung_von * 100, marker_color="#ffcc80")
            f1.add_scatter(name="Lợi nhuận kỳ vọng (triệu)", x=xs, y=s.loi_nhuan_kv / 1e6, yaxis="y2", mode="lines+markers", line=dict(color="#c62828", width=3))
            f1.update_layout(barmode="group", yaxis2=dict(overlaying="y", side="right", title="triệu VNĐ"), height=380, title="Đánh đổi theo trần rủi ro", xaxis_title="Trần nợ xấu")
            f2 = go.Figure(); f2.add_scatter(name="Nợ xấu dự đoán", x=xs, y=s.no_xau_du_doan * 100, mode="lines+markers", line=dict(color="#1565c0", width=3))
            f2.add_scatter(name="Nợ xấu thật (backtest lô)", x=xs, y=s.no_xau_that * 100, mode="lines+markers", line=dict(color="#ef6c00", dash="dash", width=3))
            f2.add_scatter(name="Trần", x=xs, y=s.tran_rui_ro * 100, mode="lines", line=dict(color="grey", dash="dot"))
            f2.update_layout(height=380, title="Nợ xấu danh mục duyệt (%)", xaxis_title="Trần nợ xấu")
            u, v = st.columns(2); u.plotly_chart(f1, use_container_width=True); v.plotly_chart(f2, use_container_width=True)
        if os.path.exists(HINH_DIR + "do_nhay_tran_rui_ro.png"): st.image(HINH_DIR + "do_nhay_tran_rui_ro.png", caption="Hình 4.3 (báo cáo) – lô chuẩn 1.000 đơn")
    st.subheader("Chi tiết lô")
    f1, f2 = st.columns(2)
    qd = f1.multiselect("Quyết định", ["Duyệt", "Từ chối"], ["Duyệt", "Từ chối"]); tg = f2.multiselect("Tầng", ["LOW", "MEDIUM", "HIGH"], ["LOW", "MEDIUM", "HIGH"])
    show = d.copy(); show["Quyết định"] = show.decision.map({1: "Duyệt", 0: "Từ chối"}); show["Tầng"] = show.risk_tier.map(tier_short)
    show = show[show["Quyết định"].isin(qd) & show["Tầng"].isin(tg)]
    out = show[["transaction_id", "customer_id", "merchant_id", "amount", "fpd_prob", "Tầng", "model_used", "fee_rate", "Quyết định", "ly_do"]].copy()
    out["amount"] = out.amount.map(vnd); out["fpd_prob"] = out.fpd_prob.map(pct); out["fee_rate"] = out.fee_rate.map(lambda v: pct(v, 1))
    st.dataframe(out, hide_index=True, use_container_width=True, height=320)
    x, y = st.columns(2)
    x.download_button("⬇ Tải CSV lô", d.to_csv(index=False).encode("utf-8-sig"), f"lo_{prm['seed']}.csv", "text/csv")
    if y.button("💾 Lưu vào FACT_DECISION_LOG"):
        try: bid = M.log_decisions(d); st.toast(f"Đã ghi {len(d)} quyết định – batch {bid}", icon="✅")
        except Exception as e: st.error(f"Không ghi được nhật ký: {e}")

# ================================================================== TAB 4
def render_tab_4():
    st.subheader("Nhật ký quyết định (FACT_DECISION_LOG)")
    log = sql("SELECT * FROM FACT_DECISION_LOG ORDER BY decided_at DESC LIMIT 500")
    if DEMO and hasattr(M, "_log") and M._log:
        log = pd.concat([d.assign(batch_id=b, fpd_probability=d.fpd_prob, fee_amount=d.amount * d.fee_rate * d.decision, decided_at="demo") for b, d in M._log])[
            ["transaction_id", "batch_id", "decision", "fpd_probability", "risk_tier", "fee_amount", "decided_at", "model_used"]]
    if len(log):
        c = st.columns(3)
        b = c[0].multiselect("batch_id", sorted(log.batch_id.unique(), reverse=True), sorted(log.batch_id.unique(), reverse=True)[:3])
        q = c[1].multiselect("Quyết định", [0, 1], [0, 1], format_func=lambda v: "Duyệt" if v else "Từ chối")
        mu = c[2].multiselect("Mô hình", sorted(log.model_used.dropna().unique()) if "model_used" in log else [], sorted(log.model_used.dropna().unique()) if "model_used" in log else [])
        f = log[log.batch_id.isin(b) & log.decision.isin(q)]
        if "model_used" in f and mu: f = f[f.model_used.isin(mu) | f.model_used.isna()]
        st.dataframe(f, hide_index=True, use_container_width=True, height=300)
        g = f.groupby(["batch_id", "decision"]).agg(so_don=("transaction_id", "size"), p_tb=("fpd_probability", "mean"), phi=("fee_amount", "sum")).reset_index()
        g["decision"] = g.decision.map({1: "Duyệt", 0: "Từ chối"}); g["p_tb"] = g.p_tb.map(pct); g["phi"] = g.phi.map(vnd)
        st.dataframe(g, hide_index=True, use_container_width=True)
    else: st.info("(không có số liệu)")
    st.subheader("Công bằng thuật toán")
    fp = BASE + "fairness.csv"
    if os.path.exists(fp):
        fa = pd.read_csv(fp); st.dataframe(fa, hide_index=True, use_container_width=True)
        if {"nhom", "ty_le_high", "no_xau_that"} <= set(fa.columns):
            st.plotly_chart(px.bar(fa, x="nhom", y=["ty_le_high", "no_xau_that"], barmode="group", title="Tỷ lệ xếp High vs nợ xấu thật theo nhóm"), use_container_width=True)
    else: st.caption("(đang cập nhật – fairness.csv chưa có)")
    st.markdown("Mô hình **không sử dụng giới tính**; khách thiếu lịch sử được chấm bằng mô hình thin-file riêng để tránh bị phạt vì thiếu dữ liệu (xem Ch.4.2 báo cáo).")
    st.subheader("Bảo vệ dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP)")
    st.markdown("1. Mọi trường định danh (tên, SĐT, thiết bị, GPS) được che bởi PrivacyGuard **trước** khi hiển thị hoặc gửi mô hình ngôn ngữ.\n"
                "2. Mô hình ngôn ngữ chỉ giải thích; quyết định đến từ mô hình dự báo + MILP và luôn có thể tái lập.\n"
                "3. Mọi quyết định được ghi nhật ký (batch_id, P, tầng, mô hình dùng, thời điểm) để truy vết/khiếu nại.")
    al = getattr(GUARD, "audit_log", [])
    st.caption(f"Phiên này đã che {len(al)} trường PII."); 
    if al: st.dataframe(pd.DataFrame(al).tail(20), hide_index=True, use_container_width=True)

with tab1: render_tab_1()
with tab2: render_tab_2()
with tab3: render_tab_3()
with tab4: render_tab_4()
