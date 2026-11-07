"""Lõi GIẢ LẬP – cùng chữ ký với model.FPDModel / llm.* để chạy giao diện khi không có dữ liệu thật.
Mọi số ở đây là ngẫu nhiên; giao diện phải hiển thị banner DEMO khi dùng module này."""
import time, numpy as np, pandas as pd
LABELS = ["1. Low Risk (An toàn - Cấp hạn mức tối đa)", "2. Medium Risk (Thăm dò - Hạn mức kiểm soát)",
          "3. High Risk (Nguy cơ - Từ chối / Chuyển AI Coach)"]
# ------------------------------------------------------------------ DEMO backend (cùng chữ ký với lõi thật)
class DemoModel:
    labels, low, high = LABELS, 0.048, 0.095
    cat_categories = {"NAME_CONTRACT_TYPE": ["Cash loans", "Revolving loans"],
                      "NAME_EDUCATION_TYPE": ["Secondary / secondary special", "Higher education", "Incomplete higher", "Lower secondary"],
                      "NAME_FAMILY_STATUS": ["Married", "Single / not married", "Civil marriage", "Separated", "Widow"],
                      "NAME_HOUSING_TYPE": ["House / apartment", "With parents", "Rented apartment", "Municipal apartment"],
                      "OCCUPATION_TYPE": ["Laborers", "Core staff", "Sales staff", "Managers", "Drivers", "Accountants"],
                      "ORGANIZATION_TYPE": ["Business Entity Type 3", "Self-employed", "Government", "Trade: type 7", "Medicine"]}
    def __init__(self): self.rng = np.random.default_rng(7); self._log = []
    def tier(self, p): return self.labels[0] if p < self.low else (self.labels[1] if p < self.high else self.labels[2])
    def _p(self, seed): return float(np.clip(np.random.default_rng(int(seed)).beta(1.2, 12), 0.005, 0.95))
    def score_customer(self, cid):
        p = 0.596 if int(cid) == 243023 else self._p(cid)
        return {"customer_id": int(cid), "p": p, "tier": self.tier(p), "source": "CUSTOMER_SCORE", "model_used": "thick"}
    def han_muc(self, p, m="thick", inc=None):
        t = self.tier(p)
        if t == self.labels[2]: return 0
        if m == "thin": return 3_000_000 if t == self.labels[0] else 1_500_000
        return 5_000_000 if t == self.labels[0] else 2_000_000
    def score_new(self, form):
        p = float(np.clip(0.25 - 0.18 * np.nanmean([form.get("EXT_SOURCE_2", np.nan), form.get("EXT_SOURCE_3", np.nan)] or [0.5]) + 0.02, 0.01, 0.9))
        return {"p": p, "tier": self.tier(p), "source": "form", "model_used": "thin", "han_muc_goi_y": self.han_muc(p, "thin")}
    def explain(self, cid=None, top=3, form=None):
        m = "thin" if form is not None else "thick"
        tang = [("ext_mean", "điểm tín nhiệm từ các nguồn bên ngoài", "thuộc nhóm 10% thấp nhất", 0.52),
                ("credit_term", "kỳ hạn vay (số kỳ trả góp)", "cao hơn phần lớn khách hàng", 0.27),
                ("annuity_income_ratio", "tỷ lệ trả góp / thu nhập", "ở mức trung bình", 0.11)]
        if m == "thick": tang.insert(0, ("ext_mean_x_ontime", "tín nhiệm kết hợp lịch sử trả đúng hạn", "thấp hơn phần lớn khách hàng", 0.90))
        return {"model_used": m,
                "tang_rui_ro": [dict(feature=f, ten=t, mo_ta=d, shap=s) for f, t, d, s in tang[:top]],
                "giam_rui_ro": [] if m == "thin" else [dict(feature="ins_late_rate", ten="tỷ lệ kỳ trả trễ", mo_ta="không ghi nhận vấn đề", shap=-0.08)],
                "goi_y": ["Bắt đầu với hạn mức thấp và theo dõi 2 kỳ đầu", "Yêu cầu bổ sung chứng từ thu nhập", "Mời tham gia AI Coach"]}
    def portfolio_summary(self):
        tiers = pd.DataFrame({"risk_tier": LABELS, "so_khach": [15466, 6711, 7823], "p_tb": [0.0248, 0.0681, 0.2002], "no_xau_that": [0.0241, 0.0709, 0.2012]})
        log = pd.DataFrame({"batch_id": ["BATCH_20261009_124257"] * 2, "decision": [0, 1], "so_don": [340, 660], "von": [945e6, 1885e6], "p_tb": [0.1599, 0.0318]})
        return {"metrics": {"auc": 0.79, "gini": 0.58, "ks": 0.4357, "pr_auc": 0.2911, "brier": 0.06547},
                "latency_ms": {"feature_store_p99": 7.57, "score_lookup_p99": 0.54}, "thresholds": {"low": 0.048, "high": 0.095}, "tiers": tiers, "decision_log": log}
    def lay_lo(self, n=1000, seed=42):
        r = np.random.default_rng(seed); p = np.clip(r.beta(1.2, 12, n), 0.003, 0.95)
        mer = r.choice(["SHOPEE", "LAZADA", "TIKTOK_SHOP", "TIKI", "GRAB", "HIGHLANDS"], n)
        fee = pd.Series(mer).map({"SHOPEE": .045, "LAZADA": .045, "TIKTOK_SHOP": .05, "TIKI": .04, "GRAB": .035, "HIGHLANDS": .03}).values
        return pd.DataFrame({"transaction_id": [f"TX{seed}_{i:05d}" for i in range(n)], "customer_id": r.integers(100000, 456000, n),
                             "amount": r.choice(np.arange(5, 101) * 1e5, n), "merchant_id": mer, "proposed_limit": r.choice([3e6, 5e6, 1e7], n),
                             "fpd_prob": p, "risk_tier": [self.tier(v) for v in p], "target_default": (r.random(n) < p).astype(int),
                             "model_used": r.choice(["thick", "thin"], n, p=[0.99, 0.01]), "fee_rate": fee,
                             "created_at": (pd.Timestamp("2026-10-10") - pd.to_timedelta(r.integers(0, 90, n), "D") + pd.to_timedelta(r.integers(6, 23, n), "h")).strftime("%Y-%m-%d %H:%M:%S")})
    def optimize(self, liquidity=2e9, risk_ceiling=0.04, lgd=0.6, n=1000, seed=42, d=None, time_limit=30):
        d = self.lay_lo(n, seed) if d is None else d.copy()
        gain = (d.fee_rate - d.fpd_prob * lgd) * d.amount
        order = np.argsort(-gain.values); sel = np.zeros(len(d), int); von = 0; risk = 0
        for i in order:
            if gain.iloc[i] <= 0: break
            a, p = d.amount.iloc[i], d.fpd_prob.iloc[i]
            if von + a <= liquidity and risk + (p - risk_ceiling) * a <= 0: sel[i] = 1; von += a; risk += (p - risk_ceiling) * a
        d["decision"] = sel
        d["ly_do"] = np.where(sel == 1, "Duyệt", np.where(d.fpd_prob * lgd >= d.fee_rate, "Không sinh lời (P×LGD ≥ phí)",
                     np.where(d.fpd_prob > risk_ceiling, "Vượt trần rủi ro danh mục", "Hết quỹ vốn / ưu tiên đơn sinh lời hơn")))
        a = d[d.decision == 1]; von = float(a.amount.sum())
        kq = {"status": "Heuristic (DEMO, không tối ưu MILP)", "solver": "DEMO", "solve_s": 0.01, "n": len(d), "tham_so": {"liquidity": liquidity, "risk_ceiling": risk_ceiling, "lgd": lgd},
              "so_don_duyet": int(len(a)), "ty_le_duyet": len(a) / len(d), "von": von, "su_dung_von": von / liquidity,
              "no_xau_du_doan": float((a.amount * a.fpd_prob).sum() / von) if von else 0, "no_xau_that": float((a.amount * a.target_default).sum() / von) if von else 0,
              "no_xau_tu_choi": float(d[d.decision == 0].target_default.mean()), "phi_mdr": float((a.amount * a.fee_rate).sum()),
              "loi_nhuan_kv": float((a.amount * (a.fee_rate - a.fpd_prob * lgd)).sum()), "loi_nhuan_that": float((a.amount * (a.fee_rate - a.target_default * lgd)).sum()),
              "rang_buoc_cham": {"thanh_khoan": von / liquidity > 0.99, "rui_ro": ((a.amount * a.fpd_prob).sum() / von if von else 0) > risk_ceiling * 0.99},
              "duyet_theo_tier": d.groupby("risk_tier")["decision"].agg(["size", "mean"]).rename(columns={"size": "so_don", "mean": "ty_le_duyet"}).to_dict("index"),
              "theo_model": d.groupby("model_used")["decision"].agg(["size", "mean"]).to_dict("index")}
        return d, kq
    def sensitivity(self, ceilings=(0.02, 0.03, 0.04, 0.05, 0.06), **kw):
        d = self.lay_lo(kw.pop("n", 1000), kw.pop("seed", 42)); rows = []
        for r in ceilings:
            _, k = self.optimize(risk_ceiling=r, d=d, **kw)
            rows.append({"tran_rui_ro": r, **{c: k[c] for c in ["so_don_duyet", "ty_le_duyet", "su_dung_von", "no_xau_du_doan", "no_xau_that", "loi_nhuan_kv", "loi_nhuan_that"]}})
        return pd.DataFrame(rows)
    def log_decisions(self, d, batch_id=None):
        bid = batch_id or f"BATCH_{time.strftime('%Y%m%d_%H%M%S')}"; self._log.append((bid, d)); return bid

class DemoLLM:
    def ask(self, system_prompt, user_content, **k): raise RuntimeError("DEMO – không có kết nối Gemini")
class DemoGuard:
    def __init__(self): self.audit_log = []
    def sanitize(self, r):
        out = dict(r)
        for k in ("full_name", "phone_number", "device_id", "last_gps_location"):
            if k in out and out[k]: out[k] = str(out[k])[:3] + "***"; self.audit_log.append({"field": k, "at": time.strftime("%H:%M:%S")})
        return out
def demo_kiem_tra_so(text, facts): return []

