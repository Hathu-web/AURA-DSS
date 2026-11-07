"""
model.py – Lớp truy cập mô hình FPD v1 cho dashboard / API.

    from model import FPDModel
    m = FPDModel(model_dir="fpd_model_v1", db_path="aura_bnpl.db")
    m.score_customer(243023)          -> dict: p, tier, decision gợi ý
    m.score_new(form_dict)            -> dict (khách mới nhập form, không có lịch sử)
    m.explain(243023, top=5)          -> dict: yếu tố tăng / giảm rủi ro (tiếng Việt, định tính)
    m.portfolio_summary()             -> dict: phân bố tier, AUC, backtest ... (từ meta.json + DB)
    m.optimize(liquidity, risk_ceiling, lgd, n=1000, seed=42) -> DataFrame lô + dict kết quả

Mọi tham số chính sách (ngưỡng, tier) đọc từ meta.json – KHÔNG hard-code.
"""
import json, os, sqlite3, time, warnings
warnings.filterwarnings("ignore", message="LightGBM binary classifier with TreeExplainer")
import numpy as np, pandas as pd, lightgbm as lgb
from features import CAT_COLS, CONTACT_COLS, DOC_COLS, NUM_COLS, REGION_COLS, ep_kieu_so, ghep_lich_su, tao_dac_trung

# Tên tiếng Việt hiển thị cho khách / cán bộ (chỉ các yếu tố có thể hành động; cố ý bỏ nhân khẩu học)
NHAN = {
    "ext_mean": "điểm tín nhiệm từ các nguồn bên ngoài", "ext_min": "điểm tín nhiệm ngoài thấp nhất",
    "ext_prod": "điểm tín nhiệm ngoài (tổng hợp)", "ext_w": "điểm tín nhiệm ngoài (có trọng số)",
    "EXT_SOURCE_1": "điểm tín nhiệm ngoài nguồn 1", "EXT_SOURCE_2": "điểm tín nhiệm ngoài nguồn 2",
    "EXT_SOURCE_3": "điểm tín nhiệm ngoài nguồn 3",
    "ext_mean_x_ontime": "điểm tín nhiệm bên ngoài kết hợp lịch sử trả đúng hạn",
    "pay_ratio_x_ext": "mức trả đủ kỳ góp kết hợp điểm tín nhiệm",
    "credit_term": "kỳ hạn quy đổi (số tiền vay / tiền trả định kỳ)", "credit_goods_ratio": "tỷ lệ số tiền vay / giá trị hàng hóa",
    "credit_income_ratio": "số tiền vay so với thu nhập năm", "annuity_income_ratio": "tiền trả định kỳ so với thu nhập",
    "total_annuity_income": "tổng nghĩa vụ trả nợ hằng tháng so với thu nhập", "AMT_ANNUITY": "tiền trả định kỳ",
    "AMT_CREDIT": "số tiền vay", "credit_minus_goods": "phần vay vượt giá trị hàng hóa",
    "ins_late_rate": "tỷ lệ kỳ trả góp bị trễ", "ins_dpd_mean": "số ngày trễ trung bình mỗi kỳ", "ins_dpd_max": "số ngày trễ dài nhất",
    "ins1y_dpd_max": "số ngày trễ dài nhất trong 12 tháng qua", "ins1y_late_rate": "tỷ lệ kỳ trễ trong 12 tháng qua",
    "ins_pay_ratio_mean": "mức trả so với số phải trả mỗi kỳ", "ins_underpaid_rate": "tỷ lệ kỳ trả thiếu",
    "ins_version_mean": "số lần thay đổi lịch trả góp",
    "bu_debt_ratio_mean": "tỷ lệ dư nợ / hạn mức tại tổ chức tín dụng khác", "bu_debt_credit_ratio": "tổng dư nợ bên ngoài so với hạn mức",
    "bu_overdue_amt_max": "số tiền từng quá hạn tại tổ chức tín dụng khác", "bu_overdue_sum": "tổng dư nợ quá hạn bên ngoài",
    "bu_active_cnt": "số khoản vay đang mở bên ngoài", "bu_days_credit_max": "thời gian từ khoản vay ngoài gần nhất",
    "bu_debt_income_ratio": "dư nợ bên ngoài so với thu nhập", "bu_recent_2y_cnt": "số khoản vay mới mở trong 2 năm",
    "bu_prolong_sum": "số lần gia hạn khoản vay bên ngoài",
    "pv_refused_rate": "tỷ lệ hồ sơ trước đây bị từ chối", "pv_app_credit_ratio_mean": "mức xin vay so với mức được duyệt trước đây",
    "pv_cnt_payment_mean": "kỳ hạn trung bình các khoản vay trước", "pv_high_interest_rate": "tỷ lệ khoản vay lãi suất cao trước đây",
    "DAYS_LAST_PHONE_CHANGE": "thời gian từ lần đổi số điện thoại",
    "credit_vs_prev_max": "số tiền vay lần này so với khoản lớn nhất trước đây",
}
GOI_Y = {
    "ins": "Thanh toán đúng hạn và đủ số tiền tất cả kỳ trả góp trong 3 tháng tới.",
    "bu": "Giảm dư nợ tại các tổ chức tín dụng khác (ưu tiên khoản đang quá hạn), tránh mở thêm khoản vay mới.",
    "pv": "Chọn mức vay sát với khả năng trả, không xin vượt mức đã được duyệt trước đây.",
    "credit_goods_ratio": "Tự thanh toán trước một phần giá trị đơn hàng.",
    "credit_term": "Chọn đơn hàng nhỏ hơn hoặc kỳ hạn phù hợp để số tiền mỗi kỳ nhẹ hơn.",
    "credit_income_ratio": "Giảm số tiền vay so với thu nhập hoặc cập nhật chứng minh thu nhập.",
    "annuity_income_ratio": "Giảm tổng số tiền phải trả mỗi tháng so với thu nhập.",
    "total_annuity_income": "Giảm tổng số tiền phải trả mỗi tháng so với thu nhập.",
    "default": "Duy trì thanh toán đúng hạn mọi khoản vay hiện có để điểm tín nhiệm được cập nhật tốt hơn.",
}
FEE_MAP = {"SHOPEE": 0.045, "LAZADA": 0.045, "TIKTOK_SHOP": 0.050, "TIKI": 0.040, "GRAB": 0.035, "HIGHLANDS": 0.030}


class FPDModel:
    def __init__(self, model_dir="fpd_model_v1", db_path="aura_bnpl.db", thin_dir=None):
        self.dir = model_dir.rstrip("/") + "/"
        self.db_path = db_path
        self.meta = json.load(open(self.dir + "meta.json", encoding="utf-8"))
        self.boosters = [lgb.Booster(model_file=self.dir + f"fold_{i}.txt") for i in range(self.meta["n_folds"])]
        self.aux = pd.read_parquet(self.dir + "aux_features.parquet")
        self.feats = self.meta["feature_names"]
        self.cat_categories = self.meta["cat_categories"]
        self.low, self.high = self.meta["tiers"]["low_max"], self.meta["tiers"]["medium_max"]
        self.labels = self.meta["tiers"]["labels"]
        self._explainers = {}
        self._pop = None  # phân phối đặc trưng toàn bộ khách (cho mô tả định tính)
        # ---- Thin-file model (khách mới, không lịch sử) – thư mục fpd_model_thin cạnh fpd_model_v1
        if thin_dir is None:
            thin_dir = os.path.join(os.path.dirname(os.path.abspath(self.dir.rstrip("/"))), "fpd_model_thin")
        self.thin_dir = thin_dir
        if self.thin_dir and os.path.isdir(self.thin_dir):
            self.thin_dir = self.thin_dir.rstrip("/") + "/"
            self.meta_thin = json.load(open(self.thin_dir + "meta.json", encoding="utf-8"))
            self.boosters_thin = [lgb.Booster(model_file=self.thin_dir + f"fold_{i}.txt") for i in range(len(self.meta_thin["best_iters"]))]
            self.feats_thin = self.meta_thin["features"]
        else:
            self.thin_dir, self.meta_thin, self.boosters_thin, self.feats_thin = None, None, None, None
        self.hist_cols = [c for c in self.feats if c.startswith(("bu_", "pv_", "ins_", "ins1y_"))]

    # ------------------------------------------------------------------ tiện ích
    def _conn(self):
        return sqlite3.connect(self.db_path)

    def tier(self, p):
        return self.labels[0] if p < self.low else (self.labels[1] if p < self.high else self.labels[2])

    RAW_EXTRA = ["DAYS_REGISTRATION", "DAYS_ID_PUBLISH", "DAYS_LAST_PHONE_CHANGE", "OWN_CAR_AGE", "HOUR_APPR_PROCESS_START",
                 "REGION_POPULATION_RELATIVE", "REGION_RATING_CLIENT_W_CITY", "OBS_30_CNT_SOCIAL_CIRCLE", "DEF_30_CNT_SOCIAL_CIRCLE",
                 "OBS_60_CNT_SOCIAL_CIRCLE", "DEF_60_CNT_SOCIAL_CIRCLE", "WEEKDAY_APPR_PROCESS_START", "NAME_TYPE_SUITE",
                 "AMT_REQ_CREDIT_BUREAU_HOUR", "AMT_REQ_CREDIT_BUREAU_DAY", "AMT_REQ_CREDIT_BUREAU_WEEK", "AMT_REQ_CREDIT_BUREAU_MON",
                 "AMT_REQ_CREDIT_BUREAU_QRT", "AMT_REQ_CREDIT_BUREAU_YEAR"]

    def _bo_sung_cot_goc(self, d):
        """Form khách mới chỉ có vài cột -> thêm mọi cột gốc còn thiếu = NaN để tao_dac_trung chạy được.
        Cờ FLAG_DOCUMENT_* / liên lạc / khu vực thiếu được coi là 0 (không nộp / không lệch)."""
        d = d.copy()
        can = set(self.meta.get("num_cols", [])) | set(self.meta.get("doc_cols", [])) | set(self.meta.get("cat_cols", [])) \
              | set(CAT_COLS) | set(NUM_COLS) | set(DOC_COLS) | set(CONTACT_COLS) | set(REGION_COLS) | set(self.RAW_EXTRA)
        for c in can:
            if c not in d.columns:
                d[c] = 0 if (c.startswith(("FLAG_DOCUMENT_", "REG_", "LIVE_")) or c in CONTACT_COLS) else np.nan
        return d

    def _features_from_raw(self, d):
        d = self._bo_sung_cot_goc(d)
        X = tao_dac_trung(d, self.cat_categories)
        return ghep_lich_su(X, d, self.aux)[self.feats]

    def _predict(self, X, model="thick"):
        bs, feats = (self.boosters, self.feats) if model == "thick" else (self.boosters_thin, self.feats_thin)
        return np.mean([b.predict(X[feats], num_threads=1) for b in bs], axis=0)

    def route(self, X) -> str:
        """Router: có bất kỳ đặc trưng lịch sử nào -> 'thick'; không -> 'thin' (nếu có mô hình thin)."""
        has_hist = X[self.hist_cols].notna().any(axis=1).iloc[0]
        return "thick" if has_hist or self.boosters_thin is None else "thin"

    # ------------------------------------------------------------------ chấm điểm
    def score_customer(self, customer_id: int) -> dict:
        """Khách có trong DIM_CUSTOMER: ưu tiên tra CUSTOMER_SCORE (0.3 ms); nếu chưa có thì tính."""
        with self._conn() as c:
            r = c.execute("SELECT fpd_probability, risk_tier FROM CUSTOMER_SCORE WHERE customer_id=?", (int(customer_id),)).fetchone()
            if r:
                return {"customer_id": int(customer_id), "p": float(r[0]), "tier": r[1], "source": "CUSTOMER_SCORE"}
            d = pd.read_sql("SELECT * FROM DIM_CUSTOMER WHERE customer_id=?", c, params=(int(customer_id),))
        if d.empty:
            raise KeyError(f"customer_id {customer_id} không tồn tại")
        d = d.rename(columns={"customer_id": "SK_ID_CURR"})
        X = self._features_from_raw(d); m = self.route(X)
        p = float(self._predict(X, m)[0])
        return {"customer_id": int(customer_id), "p": p, "tier": self.tier(p), "source": "computed", "model_used": m}

    def score_new(self, form: dict) -> dict:
        """Khách mới nhập form (dict các cột gốc, thiếu cột -> NaN). Không có lịch sử -> thin-file."""
        d = pd.DataFrame([form])
        d["SK_ID_CURR"] = -1
        X = self._features_from_raw(d); m = self.route(X)      # form không có lịch sử -> 'thin'
        p = float(self._predict(X, m)[0])
        return {"p": p, "tier": self.tier(p), "source": "form", "model_used": m,
                "han_muc_goi_y": self.han_muc(p, m, form.get("AMT_INCOME_TOTAL"))}

    def han_muc(self, p, model_used="thick", income_year=None) -> int:
        """Khuyến nghị hạn mức (VNĐ) theo tầng & luồng mô hình. Thu nhập gốc Home Credit/năm -> VNĐ/tháng = /12*1000."""
        t = self.tier(p)
        if t == self.labels[2]: return 0
        if model_used == "thin":
            return 3_000_000 if t == self.labels[0] else 1_500_000
        cap = 10_000_000 if t == self.labels[0] else 5_000_000
        if income_year: cap = int(min(cap, income_year / 12 * 1000 * 0.5))
        return int(round(cap, -5))

    # ------------------------------------------------------------------ giải thích
    def _ensure_explainers(self, model="thick"):
        if model not in self._explainers:
            import shap
            bs = self.boosters if model == "thick" else self.boosters_thin
            self._explainers[model] = [shap.TreeExplainer(b) for b in bs]
        if self._pop is None:
            with self._conn() as c:
                self._pop = pd.read_sql("SELECT * FROM FEATURE_STORE", c).drop(columns="customer_id")

    def _mo_ta(self, f, v):
        if pd.isna(v):
            return "chưa có dữ liệu"
        if f.startswith(("ins", "bu_", "pv_")) and float(v) == 0:
            return "không ghi nhận vấn đề"
        col = pd.to_numeric(self._pop[f], errors="coerce").dropna()
        pct = (col < float(v)).mean() * 100
        if pct <= 10: return "thuộc nhóm 10% thấp nhất"
        if pct <= 30: return "thấp hơn phần lớn khách hàng"
        if pct >= 90: return "thuộc nhóm 10% cao nhất"
        if pct >= 70: return "cao hơn phần lớn khách hàng"
        return "ở mức trung bình"

    def explain(self, customer_id: int = None, top: int = 3, form: dict = None) -> dict:
        """Giải thích SHAP cho khách trong CSDL (customer_id) hoặc khách mới (form)."""
        if form is not None:
            d = pd.DataFrame([form]); d["SK_ID_CURR"] = -1
        else:
            with self._conn() as c:
                d = pd.read_sql("SELECT * FROM DIM_CUSTOMER WHERE customer_id=?", c, params=(int(customer_id),))
            d = d.rename(columns={"customer_id": "SK_ID_CURR"})
        X = self._features_from_raw(d); m = self.route(X)
        self._ensure_explainers(m)
        feats = self.feats if m == "thick" else self.feats_thin
        vals = []
        for ex in self._explainers[m]:
            sv = ex.shap_values(X[feats])
            vals.append(sv[1] if isinstance(sv, list) else sv)
        s = pd.Series(np.mean(vals, axis=0)[0], index=feats)
        s = s[[f for f in s.index if f in NHAN]]
        tang = s[s > 0].sort_values(ascending=False).head(top)
        giam = s[(s < 0) & s.index.str.startswith(("ins", "bu_", "pv_"))].sort_values().head(2)
        goi_y = []
        for f in tang.index:
            k = next((k for k in ["ins", "bu", "pv"] if f.startswith(k + "_") or f.startswith(k + "1y_")), None)
            goi_y.append(GOI_Y[k] if k else GOI_Y.get(f, GOI_Y["default"]))
        goi_y = list(dict.fromkeys(goi_y + [GOI_Y["default"]]))[:3]
        return {
            "model_used": m,
            "tang_rui_ro": [{"feature": f, "ten": NHAN[f], "mo_ta": self._mo_ta(f, X[f].iloc[0]), "shap": float(tang[f])} for f in tang.index],
            "giam_rui_ro": [{"feature": f, "ten": NHAN[f], "mo_ta": self._mo_ta(f, X[f].iloc[0]), "shap": float(giam[f])} for f in giam.index],
            "goi_y": goi_y,
        }

    # ------------------------------------------------------------------ danh mục & tối ưu
    def portfolio_summary(self) -> dict:
        with self._conn() as c:
            tiers = pd.read_sql("""SELECT s.risk_tier, COUNT(*) so_khach, AVG(s.fpd_probability) p_tb, AVG(c.target_default) no_xau_that
                                   FROM CUSTOMER_SCORE s JOIN DIM_CUSTOMER c ON c.customer_id=s.customer_id GROUP BY 1 ORDER BY 1""", c)
            log = pd.read_sql("""SELECT l.batch_id, l.decision, COUNT(*) so_don, SUM(t.amount) von, AVG(l.fpd_probability) p_tb
                                 FROM FACT_DECISION_LOG l JOIN FACT_BNPL_TRANSACTION t ON t.transaction_id=l.transaction_id
                                 GROUP BY 1,2 ORDER BY 1 DESC""", c)
        return {"metrics": self.meta["metrics"], "latency_ms": self.meta.get("latency_ms", {}),
                "thresholds": {"low": self.low, "high": self.high}, "tiers": tiers, "decision_log": log}

    def lay_lo(self, n=1000, seed=42) -> pd.DataFrame:
        """Lấy 1 lô n giao dịch kèm P, tier, phí MDR và luồng mô hình (model_used)."""
        with self._conn() as c:
            tx = pd.read_sql("""SELECT t.transaction_id, t.customer_id, t.amount, t.merchant_id, t.proposed_limit,
                                       s.fpd_probability fpd_prob, s.risk_tier, c.target_default
                                FROM FACT_BNPL_TRANSACTION t JOIN CUSTOMER_SCORE s ON s.customer_id=t.customer_id
                                JOIN DIM_CUSTOMER c ON c.customer_id=t.customer_id""", c)
            d = tx.sample(n=n, random_state=seed).reset_index(drop=True)
            ids = tuple(int(i) for i in d["customer_id"])
            q = f"SELECT customer_id, ({' + '.join(f'({h} IS NOT NULL)' for h in self.hist_cols)}) n_hist FROM FEATURE_STORE WHERE customer_id IN ({','.join('?'*len(ids))})"
            nh = pd.read_sql(q, c, params=ids).set_index("customer_id")["n_hist"]
        d["model_used"] = d["customer_id"].map(lambda i: "thick" if nh.get(i, 0) > 0 else "thin")
        d["fee_rate"] = d["merchant_id"].map(FEE_MAP).fillna(0.04)
        return d

    def optimize(self, liquidity=2e9, risk_ceiling=0.04, lgd=0.6, n=1000, seed=42, d=None, time_limit=30):
        """MILP phân bổ vốn theo lô bằng PuLP/CBC. max Σ(fee−P·LGD)·A·x  s.t. ΣA·x ≤ quỹ; Σ(P−r)·A·x ≤ 0.
        Trả về (df_lô có cột decision/ly_do, dict_kết_quả). Cùng kết quả notebook: 660/1000 đơn, 43,04 triệu."""
        import pulp
        d = self.lay_lo(n, seed) if d is None else d.copy()
        amt, fee, pr = d["amount"].to_numpy(float), d["fee_rate"].to_numpy(float), d["fpd_prob"].to_numpy(float)
        m = len(d)
        prob = pulp.LpProblem("Aura_capital_allocation", pulp.LpMaximize)
        x = pulp.LpVariable.dicts("x", range(m), cat=pulp.LpBinary)
        prob += pulp.lpSum((fee[i] - pr[i] * lgd) * amt[i] * x[i] for i in range(m))
        prob += pulp.lpSum(amt[i] * x[i] for i in range(m)) <= liquidity, "thanh_khoan"
        prob += pulp.lpSum((pr[i] - risk_ceiling) * amt[i] * x[i] for i in range(m)) <= 0, "tran_rui_ro"
        t0 = time.perf_counter(); prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)); dt = time.perf_counter() - t0
        if prob.status != pulp.LpStatusOptimal:
            raise RuntimeError(f"CBC chưa chứng minh nghiệm tối ưu: {pulp.LpStatus[prob.status]}. Không ghi nhận như nghiệm tối ưu.")
        sel = np.array([int(round(x[i].value() or 0)) for i in range(m)])
        d["decision"] = sel
        d["ly_do"] = np.where(sel == 1, "Duyệt",
                     np.where(pr * lgd >= fee, "Không sinh lời (P×LGD ≥ phí)",
                     np.where(pr > risk_ceiling, "Vượt trần rủi ro danh mục", "Hết quỹ vốn / ưu tiên đơn sinh lời hơn")))
        a = d[d["decision"] == 1]; von = float(a["amount"].sum())
        # File transaction upload không có TARGET (không có nhãn quan sát):
        # tuyệt đối không báo nợ xấu/lợi nhuận “thực tế” bằng 0 do pandas.sum(skipna=True).
        has_backtest = bool(m and d["target_default"].notna().all())
        kq = {"status": pulp.LpStatus[prob.status], "solver": "PuLP/CBC", "solve_s": dt, "n": m,
              "tham_so": {"liquidity": liquidity, "risk_ceiling": risk_ceiling, "lgd": lgd},
              "so_don_duyet": int(len(a)), "ty_le_duyet": len(a) / m, "von": von, "su_dung_von": von / liquidity,
              "no_xau_du_doan": float((a["amount"] * a["fpd_prob"]).sum() / von) if von else 0,
              "no_xau_that": float((a["amount"] * a["target_default"]).sum() / von) if von and has_backtest else None,
              "no_xau_tu_choi": float(d[d["decision"] == 0]["target_default"].mean()) if has_backtest and (d["decision"] == 0).any() else None,
              "phi_mdr": float((a["amount"] * a["fee_rate"]).sum()),
              "loi_nhuan_kv": float((a["amount"] * (a["fee_rate"] - a["fpd_prob"] * lgd)).sum()),
              "loi_nhuan_that": float((a["amount"] * (a["fee_rate"] - a["target_default"] * lgd)).sum()) if has_backtest else None,
              "rang_buoc_cham": {"thanh_khoan": von / liquidity > 0.99,
                                 "rui_ro": (float((a["amount"] * a["fpd_prob"]).sum() / von) if von else 0) > risk_ceiling * 0.99},
              "duyet_theo_tier": d.groupby("risk_tier")["decision"].agg(["size", "mean"]).rename(columns={"size": "so_don", "mean": "ty_le_duyet"}).to_dict("index"),
              "theo_model": d.groupby("model_used")["decision"].agg(["size", "mean"]).to_dict("index")}
        return d, kq

    def sensitivity(self, ceilings=(0.02, 0.03, 0.04, 0.05, 0.06), **kw) -> pd.DataFrame:
        """Độ nhạy theo trần rủi ro trên cùng một lô (Hình 4.3 trên dashboard)."""
        d = self.lay_lo(kw.pop("n", 1000), kw.pop("seed", 42)); rows = []
        for r in ceilings:
            _, k = self.optimize(risk_ceiling=r, d=d, **kw)
            rows.append({"tran_rui_ro": r, **{c: k[c] for c in ["so_don_duyet", "ty_le_duyet", "su_dung_von", "no_xau_du_doan", "no_xau_that", "loi_nhuan_kv", "loi_nhuan_that"]}})
        return pd.DataFrame(rows)

    def log_decisions(self, d: pd.DataFrame, batch_id: str = None) -> str:
        """Ghi lô đã quyết định vào FACT_DECISION_LOG (có model_used). Trả về batch_id."""
        batch_id = batch_id or f"BATCH_{time.strftime('%Y%m%d_%H%M%S')}"; now = time.strftime("%Y-%m-%d %H:%M:%S")
        recs = [(r.transaction_id, batch_id, int(r.decision), round(float(r.fpd_prob), 6), r.risk_tier,
                 round(float(r.amount) * r.fee_rate, 2) if r.decision == 1 else 0.0, now, r.model_used) for r in d.itertuples()]
        with self._conn() as c:
            if "model_used" not in [r[1] for r in c.execute("PRAGMA table_info(FACT_DECISION_LOG)")]:
                c.execute("ALTER TABLE FACT_DECISION_LOG ADD COLUMN model_used TEXT")
            c.executemany("""INSERT OR REPLACE INTO FACT_DECISION_LOG
                (transaction_id, batch_id, decision, fpd_probability, risk_tier, fee_amount, decided_at, model_used)
                VALUES (?,?,?,?,?,?,?,?)""", recs)
        return batch_id
