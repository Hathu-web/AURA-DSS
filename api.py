# =====================================================================================
#  AURA DSS – Backend FastAPI. Bọc lõi thật (model.FPDModel, llm.*) và phục vụ web build (React).
#  Chạy:  uvicorn api:app --host 0.0.0.0 --port 8000          (Colab: xem HUONG_DAN_CHAY.md)
#  Biến môi trường: AURA_BASE (thư mục chứa fpd_model_v1/, aura_bnpl.db, hinh/), AURA_DEMO=1 để ép demo,
#                   GEMINI_API_KEY (chỉ ở server – KHÔNG bao giờ gửi xuống trình duyệt).
# =====================================================================================
import os, io, re, json, time, sqlite3, uuid, traceback
from typing import Optional, List, Dict, Any
from pathlib import Path
import math
import numpy as np, pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

# Đường dẫn độc lập hệ điều hành (AURA_BASE có/không có dấu / ở cuối đều đúng).
PROJECT_DIR = Path(__file__).resolve().parent
BASE = Path(os.environ.get("AURA_BASE", str(PROJECT_DIR))).expanduser().resolve()
MODEL_DIR, DB_PATH, HINH_DIR = str(BASE / "fpd_model_v1"), str(BASE / "aura_bnpl.db"), str(BASE / "hinh")
ACCESS_TOKEN = os.environ.get("AURA_ACCESS_TOKEN", "").strip()
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_build")
FORCE_DEMO = os.environ.get("AURA_DEMO", "0") == "1"
# Evidence can be displayed in DEMO independently of trained model artifacts.
# Never pretend that a metadata-only directory can run LightGBM without fold files.
EVIDENCE_DIR = PROJECT_DIR / "evaluation_artifacts"

def _read_meta(*paths):
    for path in paths:
        if path.exists():
            try:
                with path.open(encoding="utf-8") as handle:
                    return json.load(handle), str(path)
            except (OSError, ValueError):
                continue
    return {}, None

META_V1, META_V1_SOURCE = _read_meta(BASE / "fpd_model_v1" / "meta.json", EVIDENCE_DIR / "meta_v1.json")
META_THIN, META_THIN_SOURCE = _read_meta(BASE / "fpd_model_thin" / "meta.json", EVIDENCE_DIR / "meta_thin_v2.json")
metrics = META_V1.get("metrics", {})
latencies = META_V1.get("latency_ms", {})
router_metrics = META_V1.get("router_metrics", {})
SO_TINH = {"auc_thick": metrics.get("auc", 0.7900), "auc_thin": META_THIN.get("metrics", {}).get("auc") or 0.7704,
           "gini": metrics.get("gini", .58), "ks": metrics.get("ks", .4357),
           "pr_auc": metrics.get("pr_auc", .2911), "brier": metrics.get("brier", .06547),
           "no_xau_backtest": 2.86, "no_xau_nen": 8.07,
           "p99_ms": latencies.get("model_p99"),
           "p99_end_to_end_ms": latencies.get("end_to_end_p99"),
           "p99_feature_store_ms": latencies.get("feature_store_p99"),
           "auc_router_holdout": router_metrics.get("auc_holdout"),
           "n_features_thick": len(META_V1.get("feature_names", [])) or None,
           "n_features_thin": META_THIN.get("n_features", len(META_THIN.get("features", [])) or None),
           "n_train": 246005, "n_holdout": 61502}

SYSTEM_PROMPT = ("Bạn là trợ lý phân tích của hệ hỗ trợ ra quyết định tín dụng BNPL Aura. Chỉ dùng số liệu có trong FACTS; "
                 "nếu thiếu, ghi '(không có số liệu)'. Trả lời tiếng Việt, ngắn gọn (≤ 150 từ), có số cụ thể, kết thúc bằng 1 khuyến nghị. "
                 "Không tự thay đổi tầng rủi ro, xác suất hay quyết định đã cho.")

# ------------------------------------------------------------------ nạp lõi
DEMO, DEMO_REASON = True, ""
try:
    if FORCE_DEMO: raise RuntimeError("AURA_DEMO=1")
    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from model import FPDModel
    from llm import LLM, PrivacyGuard, kiem_tra_so
    M = FPDModel(model_dir=MODEL_DIR, db_path=DB_PATH); GUARD = PrivacyGuard(); KIEM_TRA_SO = kiem_tra_so
    try: LLM_ = LLM()
    except Exception as e:
        from demo_core import DemoLLM; LLM_ = DemoLLM(); DEMO_REASON = f"LLM không khả dụng: {e}"
    DEMO = False
except Exception as e:
    from demo_core import DemoModel, DemoLLM, DemoGuard, demo_kiem_tra_so
    M, LLM_, GUARD, KIEM_TRA_SO = DemoModel(), DemoLLM(), DemoGuard(), demo_kiem_tra_so
    DEMO_REASON = f"{type(e).__name__}: {e}"

app = FastAPI(title="Aura DSS API", version="1.0")
# Frontend đã được serve same-origin; Vite dùng proxy nên không cần CORS mở toàn Internet.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Aura-Token"])

@app.middleware("http")
async def api_access_gate(request: Request, call_next):
    """Token tùy chọn: khi chia sẻ công khai, bảo vệ toàn bộ API dữ liệu/ghi, trừ health và mẫu CSV."""
    import hmac
    if (ACCESS_TOKEN and request.url.path.startswith("/api/")
            and request.url.path not in {"/api/health", "/api/sample_csv"}
            and not hmac.compare_digest(request.headers.get("X-Aura-Token", ""), ACCESS_TOKEN)):
        return JSONResponse(status_code=401, content={"detail": "Thiếu hoặc sai mã truy cập API"})
    return await call_next(request)
RUNS: Dict[str, pd.DataFrame] = {}          # kết quả optimize chờ ghi log (run_id -> df)

def require_private(x_aura_token: Optional[str] = Header(default=None)):
    """Khi công khai qua tunnel, đặt AURA_ACCESS_TOKEN; không có token thì chỉ dùng local/demo."""
    import hmac
    if ACCESS_TOKEN and not hmac.compare_digest(x_aura_token or "", ACCESS_TOKEN):
        raise HTTPException(status_code=401, detail="Thiếu hoặc sai AURA_ACCESS_TOKEN")

def parse_dates(d_from, d_to):
    try:
        a = pd.Timestamp(d_from) if d_from else None
        b = pd.Timestamp(d_to) if d_to else None
        if a is not None and (a != a.normalize()): raise ValueError()
        if b is not None and (b != b.normalize()): raise ValueError()
        if a is not None and b is not None and a > b:
            raise HTTPException(422, "Ngày bắt đầu phải trước hoặc bằng ngày kết thúc")
        return a, b
    except HTTPException: raise
    except (ValueError, TypeError): raise HTTPException(422, "Ngày phải có định dạng YYYY-MM-DD")

# ------------------------------------------------------------------ tiện ích
def js(o):
    """Chuyển numpy/pandas/NaN sang JSON an toàn."""
    if isinstance(o, pd.DataFrame): return [js(r) for r in o.to_dict("records")]
    if isinstance(o, pd.Series): return js(o.to_dict())
    if isinstance(o, dict): return {str(k): js(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, np.ndarray)): return [js(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating, float)): return float(o) if math.isfinite(float(o)) else None
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, pd.Timestamp): return o.strftime("%Y-%m-%d %H:%M:%S")
    return o

def sql(q, params=()):
    with sqlite3.connect(DB_PATH) as c: return pd.read_sql(q, c, params=params)

def tier_code(t): return {"1": "LOW", "2": "MEDIUM", "3": "HIGH"}.get(str(t)[:1], "NA")

def tx_in_range(d_from: Optional[str], d_to: Optional[str]) -> pd.DataFrame:
    """Giao dịch (có created_at) + điểm + tầng + quyết định mới nhất trong khoảng thời gian."""
    if DEMO:
        d = M.lay_lo(6000, 7); d["decision"] = (d.fpd_prob < 0.07).astype(int); d["customer_name"] = None
    else:
        d = sql("""SELECT t.transaction_id, t.customer_id, t.amount, t.merchant_id, t.proposed_limit, t.created_at,
                          s.fpd_probability fpd_prob, s.risk_tier, c.target_default,
                          (SELECT l.decision FROM FACT_DECISION_LOG l WHERE l.transaction_id=t.transaction_id ORDER BY l.decided_at DESC LIMIT 1) decision,
                          (SELECT l.model_used FROM FACT_DECISION_LOG l WHERE l.transaction_id=t.transaction_id ORDER BY l.decided_at DESC LIMIT 1) model_used
                   FROM FACT_BNPL_TRANSACTION t JOIN CUSTOMER_SCORE s ON s.customer_id=t.customer_id
                   JOIN DIM_CUSTOMER c ON c.customer_id=t.customer_id""")
        d["fee_rate"] = d["merchant_id"].map(getattr(__import__("model"), "FEE_MAP")).fillna(0.04)
    d["created_at"] = pd.to_datetime(d["created_at"])
    a, b = parse_dates(d_from, d_to)
    if a is not None: d = d[d.created_at >= a]
    if b is not None: d = d[d.created_at < b + pd.Timedelta(days=1)]
    d["tier"] = d["risk_tier"].map(tier_code)
    return d.reset_index(drop=True)

def doi_ky(d_from, d_to):
    """Khoảng kỳ trước có cùng độ dài để tính delta."""
    if not (d_from and d_to): return None, None
    a, b = pd.Timestamp(d_from), pd.Timestamp(d_to); n = (b - a).days + 1
    return (a - pd.Timedelta(days=n)).strftime("%Y-%m-%d"), (a - pd.Timedelta(days=1)).strftime("%Y-%m-%d")

def kpi_cua(d: pd.DataFrame) -> dict:
    von = float(d.amount.sum()); duyet = d[d.decision == 1]
    return {"so_giao_dich": int(len(d)), "gia_tri": von, "p_tb": float(d.fpd_prob.mean()) if len(d) else None,
            "ty_le_high": float((d.tier == "HIGH").mean()) if len(d) else None,
            "ty_le_duyet": float((d.decision == 1).mean()) if d.decision.notna().any() else None,
            "von_duyet": float(duyet.amount.sum()),
            "no_xau_du_doan_duyet": float((duyet.amount * duyet.fpd_prob).sum() / duyet.amount.sum()) if len(duyet) else None,
            "no_xau_that_duyet": float((duyet.amount * duyet.target_default).sum() / duyet.amount.sum()) if len(duyet) else None,
            "phi_mdr": float((duyet.amount * duyet.fee_rate).sum()) if "fee_rate" in d else None}

# ------------------------------------------------------------------ schemas
class FormMoi(BaseModel): form: Dict[str, Any]
class OptimizeReq(BaseModel):
    liquidity: float = Field(2e9, gt=0, le=1e11)
    risk_ceiling: float = Field(0.04, ge=0.005, le=0.30)
    lgd: float = Field(0.6, ge=0, le=1)
    n: int = Field(1000, ge=1, le=2000)
    seed: int = Field(42, ge=0, le=2_147_483_647)
    d_from: Optional[str] = None; d_to: Optional[str] = None
class SensReq(OptimizeReq): ceilings: List[float] = Field(default_factory=lambda: [0.02, 0.03, 0.04, 0.05, 0.06], min_length=1, max_length=10)
class LogReq(BaseModel): run_id: str; batch_id: Optional[str] = None
class AskReq(BaseModel): question: str = Field(min_length=2, max_length=500); d_from: Optional[str] = None; d_to: Optional[str] = None; customer_id: Optional[int] = None
class AgentReq(AskReq): confirm: bool = False   # Agentic RAG: confirm=True mới cho phép run_milp ghi nhật ký quyết định

# ------------------------------------------------------------------ endpoints
@app.get("/api/health")
def health():
    d = tx_in_range(None, None)
    return {"demo": DEMO, "reason": DEMO_REASON, "data_mode": "synthetic_demo" if DEMO else "home_credit_holdout_plus_simulated_bnpl", "source_note": "TARGET lịch sử Home Credit, không phải FPD thực tế của BNPL", "labels": M.labels, "thresholds": {"low": M.low, "high": M.high},
            "models": {"thick": {"features": 188, "auc": SO_TINH["auc_thick"]}, "thin": {"features": len(M.feats_thin) if getattr(M, "feats_thin", None) else 82, "auc": SO_TINH["auc_thin"]},
                       "milp": "PuLP/CBC"}, "so_tinh": SO_TINH, "cat_categories": getattr(M, "cat_categories", {}),
            "time_range": js(d.created_at.agg(["min", "max"])),
            "data_to": str(d.created_at.max())[:10], "data_from": str(d.created_at.min())[:10]}

@app.get("/api/summary")
def summary(d_from: Optional[str] = None, d_to: Optional[str] = None):
    d = tx_in_range(d_from, d_to)
    pf, pt = doi_ky(d_from, d_to); prev = kpi_cua(tx_in_range(pf, pt)) if pf else None
    daily = d.assign(ngay=d.created_at.dt.strftime("%Y-%m-%d")).groupby("ngay").agg(
        so_gd=("transaction_id", "size"), gia_tri=("amount", "sum"), p_tb=("fpd_prob", "mean"),
        ty_le_duyet=("decision", "mean"), high=("tier", lambda s: (s == "HIGH").mean())).reset_index()
    tiers = d.groupby("tier").agg(so=("transaction_id", "size"), p_tb=("fpd_prob", "mean"), bad=("target_default", "mean"),
                                  gia_tri=("amount", "sum"), duyet=("decision", "mean")).reset_index()
    merch = d.groupby("merchant_id").agg(so=("transaction_id", "size"), gia_tri=("amount", "sum"), p_tb=("fpd_prob", "mean"),
                                         high=("tier", lambda s: (s == "HIGH").mean()), duyet=("decision", "mean")).reset_index().sort_values("gia_tri", ascending=False)
    heat = d.pivot_table(index="merchant_id", columns="tier", values="transaction_id", aggfunc="size", fill_value=0).reset_index()
    hist = np.histogram(d.fpd_prob.dropna().clip(0, 0.5), bins=25, range=(0, 0.5))
    funnel = [{"buoc": "Tổng giao dịch", "so": int(len(d))}, {"buoc": "Qua sàng lọc rủi ro", "so": int((d.tier != "HIGH").sum())},
              {"buoc": "Đề xuất phân bổ", "so": int((d.decision == 1).sum())},
              {"buoc": "Hậu kiểm tốt (tham chiếu)", "so": int(((d.decision == 1) & (d.target_default == 0)).sum())}]
    ps = M.portfolio_summary()
    return js({"kpi": kpi_cua(d), "kpi_truoc": prev, "daily": daily, "tiers": tiers, "merchants": merch, "heatmap": heat,
               "hist": {"bins": hist[1].tolist(), "counts": hist[0].tolist()}, "funnel": funnel,
               "portfolio": {"tiers": ps["tiers"], "metrics": ps.get("metrics"), "latency_ms": ps.get("latency_ms")},
               "model_mix": d.model_used.value_counts(dropna=True).to_dict() if "model_used" in d else {}})

@app.get("/api/transactions")
def transactions(d_from: Optional[str] = None, d_to: Optional[str] = None, tier: Optional[str] = None,
                 merchant: Optional[str] = None, limit: int = Query(200, ge=1, le=1000), q: Optional[str] = None, sort: str = "created_at"):
    d = tx_in_range(d_from, d_to)
    if tier: d = d[d.tier == tier.upper()]
    if merchant: d = d[d.merchant_id == merchant]
    if q: d = d[d.transaction_id.astype(str).str.contains(q, regex=False) | d.customer_id.astype(str).str.contains(q, regex=False)]
    if sort not in {"created_at", "fpd_prob", "amount", "customer_id", "transaction_id"}: sort = "created_at"
    # TARGET là nhãn hậu kiểm; không đưa vào bảng tra cứu quyết định cá nhân.
    return js({"total": int(len(d)), "rows": d.drop(columns=["target_default", "customer_name"], errors="ignore").sort_values(sort, ascending=False).head(limit)})

@app.get("/api/score/{customer_id}")
def score(customer_id: int):
    try: s = M.score_customer(customer_id)
    except KeyError: raise HTTPException(404, f"customer_id {customer_id} không tồn tại")
    ex = M.explain(customer_id)
    khach = None
    if not DEMO:
        pii = sql("SELECT full_name, phone_number, device_id, last_gps_location FROM DIM_CUSTOMER_PII WHERE customer_id=?", (customer_id,))
        if len(pii): khach = GUARD.sanitize(pii.iloc[0].to_dict())
        ho_so = sql("SELECT AMT_INCOME_TOTAL, AMT_CREDIT, AMT_ANNUITY, DAYS_BIRTH, DAYS_EMPLOYED, NAME_EDUCATION_TYPE, NAME_FAMILY_STATUS, OCCUPATION_TYPE FROM DIM_CUSTOMER WHERE customer_id=?", (customer_id,))
        ho_so = ho_so.iloc[0].to_dict() if len(ho_so) else {}
        ho_so["thu_nhap_thang_vnd"] = ho_so.get("AMT_INCOME_TOTAL", 0) / 12 * 1000 if ho_so else None
        ho_so["tuoi"] = round(-ho_so["DAYS_BIRTH"] / 365.25) if ho_so.get("DAYS_BIRTH") else None
    else: ho_so = {"thu_nhap_thang_vnd": 14_500_000, "tuoi": 31}
    m_used = s.get("model_used") or ex.get("model_used", "thick")
    han_muc = M.han_muc(s["p"], m_used, ho_so.get("AMT_INCOME_TOTAL") if ho_so else None)
    return js({**s, "tier_code": tier_code(s["tier"]), "model_used": m_used, "han_muc": han_muc, "explain": ex, "khach": khach, "ho_so": ho_so})

@app.post("/api/score_new")
def score_new(req: FormMoi):
    try:
        s = M.score_new(req.form); ex = M.explain(form=req.form)
    except Exception as e:
        raise HTTPException(400, f"Không chấm được hồ sơ: {e}")
    return js({**s, "tier_code": tier_code(s["tier"]), "han_muc": s.get("han_muc_goi_y"), "explain": ex})

@app.post("/api/optimize")
def optimize(req: OptimizeReq):
    d = None
    if req.d_from or req.d_to:                       # lô theo khoảng thời gian thay vì seed
        base = tx_in_range(req.d_from, req.d_to)
        if len(base) == 0: raise HTTPException(400, "Không có giao dịch trong khoảng này")
        d = base.sample(n=min(req.n, len(base)), random_state=req.seed).reset_index(drop=True)
        if "model_used" not in d or d.model_used.isna().all(): d["model_used"] = "thick"
    df, kq = M.optimize(liquidity=req.liquidity, risk_ceiling=req.risk_ceiling, lgd=req.lgd, n=req.n, seed=req.seed, d=d)
    run_id = uuid.uuid4().hex[:8]; RUNS[run_id] = df
    df["tier"] = df.risk_tier.map(tier_code)
    ly_do = df[df.decision == 0].ly_do.value_counts().to_dict()
    by_merch = df.groupby("merchant_id").agg(so=("decision", "size"), duyet=("decision", "mean"), von=("amount", lambda s: s[df.loc[s.index, "decision"] == 1].sum())).reset_index()
    return js({"run_id": run_id, "kq": kq, "ly_do_tu_choi": ly_do, "theo_merchant": by_merch,
               "rows": df.drop(columns=[c for c in ["created_at"] if c in df]).head(1000)})

@app.post("/api/sensitivity")
def sensitivity(req: SensReq):
    d = None
    if req.d_from or req.d_to:
        base = tx_in_range(req.d_from, req.d_to); d = base.sample(n=min(req.n, len(base)), random_state=req.seed).reset_index(drop=True)
    rows = []
    if any(not 0.005 <= r <= 0.30 for r in req.ceilings): raise HTTPException(422, "Trần rủi ro phải nằm trong [0.5%, 30%]")
    for r in req.ceilings:
        _, k = M.optimize(liquidity=req.liquidity, risk_ceiling=r, lgd=req.lgd, n=req.n, seed=req.seed, d=d)
        rows.append({"tran_rui_ro": r, **{c: k[c] for c in ["so_don_duyet", "ty_le_duyet", "su_dung_von", "no_xau_du_doan", "no_xau_that", "loi_nhuan_kv", "loi_nhuan_that"]}})
    # độ nhạy theo quỹ vốn (cùng trần mặc định)
    rows_q = []
    for q in [1.0e9, 1.5e9, 2.0e9, 2.5e9, 3.0e9]:
        _, k = M.optimize(liquidity=q, risk_ceiling=req.risk_ceiling, lgd=req.lgd, n=req.n, seed=req.seed, d=d)
        rows_q.append({"quy": q, **{c: k[c] for c in ["so_don_duyet", "ty_le_duyet", "su_dung_von", "no_xau_du_doan", "loi_nhuan_kv"]}})
    return js({"theo_tran": rows, "theo_quy": rows_q})

@app.post("/api/log")
def log(req: LogReq, _=Depends(require_private)):
    df = RUNS.get(req.run_id)
    if df is None: raise HTTPException(404, "run_id không tồn tại hoặc đã hết hạn")
    # Không ghi một run hai lần: bảo vệ nhật ký khỏi ghi trùng.
    bid = M.log_decisions(df, req.batch_id)
    RUNS.pop(req.run_id, None)
    return {"batch_id": bid, "so_don": int(len(df))}

@app.get("/api/decision_log")
def decision_log(limit: int = Query(500, ge=1, le=2000), batch_id: Optional[str] = None):
    if DEMO:
        out = [d.assign(batch_id=b, fpd_probability=d.fpd_prob, fee_amount=d.amount * d.fee_rate * d.decision, decided_at="demo") for b, d in getattr(M, "_log", [])]
        df = pd.concat(out, ignore_index=True)[["transaction_id", "batch_id", "decision", "fpd_probability", "risk_tier", "fee_amount", "decided_at", "model_used"]] if out else pd.DataFrame()
        if batch_id and len(df): df = df[df.batch_id == batch_id]
        df = df.tail(limit)
    else:
        df = sql("SELECT * FROM FACT_DECISION_LOG" + (" WHERE batch_id=?" if batch_id else "") + " ORDER BY decided_at DESC LIMIT ?", ((batch_id, limit) if batch_id else (limit,)))
    batches = df.groupby("batch_id").agg(so_don=("transaction_id", "size"), duyet=("decision", "mean"), p_tb=("fpd_probability", "mean"), phi=("fee_amount", "sum"), luc=("decided_at", "max")).reset_index().sort_values("luc", ascending=False) if len(df) else []
    return js({"rows": df, "batches": batches})


# ---- chuẩn hoá bảng fairness (CSV sinh ở Colab có thể đặt tên cột khác nhau) ----
FAIRNESS_MAU = [dict(nhom_loai=a, nhom=b, n=n, p_tb=p/100, bad=bad/100, false_reject=fr/100) for a, b, n, p, bad, fr in [
    ("Nhóm tuổi", "<25", 1238, 12.25, 10.74, 45.5), ("Nhóm tuổi", "25-34", 15000, 9.9, 9.92, 33.0), ("Nhóm tuổi", "35-44", 16000, 8.1, 8.34, 22.7), ("Nhóm tuổi", "45-54", 14000, 7.0, 7.18, 19.2), ("Nhóm tuổi", "55+", 15000, 5.27, 5.27, 11.8),
    ("Học vấn", "Higher education", 15000, 5.4, 5.36, 13.3), ("Học vấn", "Incomplete higher", 2000, 8.9, 8.47, 28.0), ("Học vấn", "Lower secondary", 760, 11.1, 10.87, 36.1), ("Học vấn", "Secondary", 43000, 8.9, 9.01, 25.6),
    ("Vùng", "Region 1", 6500, 4.9, 4.68, 10.2), ("Vùng", "Region 2", 45000, 7.9, 7.94, 22.3), ("Vùng", "Region 3", 10000, 11.1, 11.39, 33.3)]]

def chuan_hoa_fairness(f: pd.DataFrame):
    f = f.copy(); obj = [c for c in f.columns if f[c].dtype == object]; num = [c for c in f.columns if c not in obj]
    ren = {}
    # The official fairness.csv stores subgroup in 'nhom' and dimension in 'tieu_chi'.
    # Do not infer roles from column position (doing so reverses chart grouping).
    if "nhom" in f.columns and "tieu_chi" in f.columns:
        ren["tieu_chi"] = "nhom_loai"
    elif len(obj) >= 2:
        ren[obj[0]], ren[obj[1]] = "nhom_loai", "nhom"
    elif len(obj) == 1:
        ren[obj[0]] = "nhom"
        f["nhom_loai"] = "Nhóm"
    def pick(pats):
        for c in num:
            if any(re.search(p, c, re.I) for p in pats) and c not in ren: return c
    for k, pats in {"n": [r"^n$", r"so_khach", r"count", r"^n_"], "p_tb": [r"pred", r"p_tb", r"p_du_doan", r"p_mean"], "bad": [r"actual", r"bad", r"no_xau", r"default_rate"],
                    "high": [r"high"], "false_reject": [r"false_rej", r"khach_tot", r"tu_choi_oan", r"\bfr\b", r"fnr"], "gap": [r"gap", r"chenh", r"lech_hieu_chuan_pt"]}.items():
        c = pick(pats)
        if c: ren[c] = k
    f = f.rename(columns=ren)
    for c in ["p_tb", "bad", "high", "false_reject"]:                 # % -> tỷ lệ nếu cần
        if c in f and f[c].abs().max() > 1.5: f[c] = f[c] / 100
    return js(f)

def evaluation_csv_path(filename: str) -> Path:
    """Prefer current AURA_BASE; use packaged evidence if models/DB reside elsewhere."""
    primary = BASE / filename
    return primary if primary.is_file() else PROJECT_DIR / filename

@app.get("/api/evaluation")
def evaluation():
    """Bảng baseline (Ch.6) + công bằng (Ch.7) đọc từ CSV sinh ở Colab; demo -> số trong báo cáo."""
    fb, ff = evaluation_csv_path("baseline_comparison.csv"), evaluation_csv_path("fairness.csv")
    out = {"so_tinh": SO_TINH,
           "evaluation_note": "CSV và metadata là dữ liệu kiểm chứng của notebook; không phải giao dịch BNPL thực. AUC Thin-file thiếu trong metadata được để trống.",
           "metadata_v1_source": "json" if META_V1_SOURCE else "reference_only",
           "metadata_thin_source": "json" if META_THIN_SOURCE else "reference_only",
           "baseline_source": "csv" if fb.exists() else "reference_only",
           "fairness_source": "csv" if ff.exists() else "reference_only"}
    if os.path.exists(fb):
        b = pd.read_csv(fb); rows = []
        for quy, g in b.groupby("quy_ty"):
            for pa in sorted({c.split("|")[0] for c in g.columns if "|" in c}):
                rows.append({"quy_ty": quy, "phuong_an": pa, **{c.split("|")[1]: float(g[c].mean()) for c in g.columns if c.startswith(pa + "|")}})
        out["baseline"] = rows
        out["baseline_runs"] = len(b)
        out["baseline_seeds_per_fund"] = {str(k): int(len(g)) for k, g in b.groupby("quy_ty")}
    else:
        out["baseline"] = [dict(quy_ty=2.0, phuong_an=p, ty_le_duyet=a, su_dung_von=b_, no_xau_that_gia_tri=c, loi_nhuan_that_trieu=d_, loi_nhuan_tren_1ty=e, khach_tot_bi_tu_choi=f)
                           for p, a, b_, c, d_, e, f in [("B0 Duyệt tất cả (FIFO)", .7135, 1, .0763, -9.79, -4.9, .2874), ("B1 Quy tắc thủ công", .5479, .8652, .0398, 29.54, 17.03, .4311),
                                                        ("B2 Mô hình + ngưỡng, FIFO", .7088, .9999, .0345, 40.25, 20.13, .2587), ("B3 Aura: tầng + MILP", .6261, .8619, .0279, 42.48, 24.66, .3405)]] + \
                          [dict(quy_ty=1.5, phuong_an=p, ty_le_duyet=a, su_dung_von=1, no_xau_that_gia_tri=c, loi_nhuan_that_trieu=d_, loi_nhuan_tren_1ty=e, khach_tot_bi_tu_choi=f)
                           for p, a, c, d_, e, f in [("B0 Duyệt tất cả (FIFO)", .5357, .0763, -7.32, -4.88, .4653), ("B1 Quy tắc thủ công", .475, .0402, 25.18, 16.79, .5067),
                                                     ("B2 Mô hình + ngưỡng, FIFO", .5306, .0363, 28.68, 19.12, .4463), ("B3 Aura: tầng + MILP", .5354, .0235, 41.51, 27.67, .4337)]]
    if ff.exists():
        raw_fairness = pd.read_csv(ff)
        out["fairness"] = chuan_hoa_fairness(raw_fairness)
        out["fairness_coverage"] = {str(k): int(g["so_khach"].sum()) for k, g in raw_fairness.groupby("tieu_chi")} if {"tieu_chi", "so_khach"} <= set(raw_fairness.columns) else {}
    else:
        out["fairness"] = FAIRNESS_MAU
        out["fairness_coverage"] = {}
    # The ablation figures below came from the original Dashboard, not the supplied two JSONs.
    out["thin_vs_thick_source"] = "reference_only"
    out["thin_vs_thick"] = [{"kich_ban": "Thick-file, đủ lịch sử", "auc": .79, "brier": .0655, "p_tb": .0795, "high": .258, "bad_low": .0241},
                            {"kich_ban": "Thick-file, lịch sử bị che", "auc": .757, "brier": .0683, "p_tb": .0919, "high": .349, "bad_low": .0186},
                            {"kich_ban": "Thin-file (86 đặc trưng)", "auc": .7704, "brier": .0669, "p_tb": .08, "high": .267, "bad_low": .0252}]
    out["tiers_holdout"] = [{"tier": "LOW", "share": .52, "bad": .0241}, {"tier": "MEDIUM", "share": .222, "bad": .0709}, {"tier": "HIGH", "share": .258, "bad": .2033}]
    out["importance_groups"] = {"application": .44, "previous": .129, "bureau": .117, "installments": .116, "khác": .198}
    return out

@app.get("/api/pii_audit")
def pii_audit(): return js({"audit": list(getattr(GUARD, "audit_log", []))[-50:], "so_lan": len(getattr(GUARD, "audit_log", []))})

# ---------------------------------------------------------------- chatbot: facts có cấu trúc + (tuỳ chọn) SQL rào chắn
BANG_CHO_PHEP = {"FACT_BNPL_TRANSACTION", "FACT_DECISION_LOG", "CUSTOMER_SCORE", "DIM_CUSTOMER", "FEATURE_STORE"}
SQL_GUIDE = """Các bảng được phép (SQLite): FACT_BNPL_TRANSACTION(transaction_id, customer_id, amount, merchant_id, proposed_limit, created_at),
CUSTOMER_SCORE(customer_id, fpd_probability, risk_tier), FACT_DECISION_LOG(transaction_id, batch_id, decision, fpd_probability, risk_tier, fee_amount, decided_at, model_used),
DIM_CUSTOMER(customer_id, AMT_INCOME_TOTAL, DAYS_BIRTH, NAME_EDUCATION_TYPE, NAME_FAMILY_STATUS, OCCUPATION_TYPE, REGION_RATING_CLIENT, target_default).
risk_tier bắt đầu bằng '1.' (Low) '2.' (Medium) '3.' (High). Chỉ viết MỘT câu SELECT, có LIMIT ≤ 200, không dùng bảng khác."""

def sql_an_toan(q: str) -> Optional[str]:
    if not isinstance(q, str) or len(q) > 3000: return None
    q = q.strip().strip("`").strip(); q = re.sub(r"^sql\s*", "", q, flags=re.I)
    if not re.match(r"^\s*select\b", q, re.I) or ";" in q.rstrip(";"): return None
    if re.search(r"\b(insert|update|delete|drop|alter|attach|pragma|create)\b", q, re.I): return None
    bang = set(re.findall(r"\b(?:from|join)\s+([A-Za-z_]+)", q, re.I))
    if not bang or not bang <= BANG_CHO_PHEP: return None
    # Giới hạn kết quả; query_only khóa thao tác ghi ở tầng SQLite.
    limit = re.search(r"\blimit\s+(\d+)", q, re.I)
    if limit and int(limit.group(1)) > 200: return None
    if not limit: q = q.rstrip(";") + " LIMIT 200"
    return q.rstrip(";")


def tra_loi_ngoai_tuyen(q, k, facts, d):
    """Trả lời dựa trên FACTS khi không có LLM: chọn mẫu câu theo từ khoá."""
    ql = q.lower(); tt = facts["theo_tang"]; tm = facts["theo_merchant"]
    fmtp = lambda v, dp=2: f"{v*100:.{dp}f} %" if v is not None else "chưa có số liệu"
    chung = (f"Trong khoảng đã chọn có **{k['so_giao_dich']}** giao dịch, P trung bình **{fmtp(k['p_tb'])}**, "
             f"tỷ lệ High **{fmtp(k['ty_le_high'],1)}**, tỷ lệ đề xuất chọn **{fmtp(k['ty_le_duyet'],1)}**, "
             f"rủi ro dự đoán của phần đã chọn **{fmtp(k['no_xau_du_doan_duyet'])}**.")
    if "khach" in facts and isinstance(facts["khach"], dict):
        kh = facts["khach"]; ex = kh.get("explain", {}); yt = ", ".join(x["ten"] for x in ex.get("tang_rui_ro", [])[:3])
        return f"Khách **{kh['customer_id']}** có P(default) **{kh['p']*100:.1f} %** → tầng **{kh['tier_code']}** ({kh['model_used']}-file). Yếu tố tăng rủi ro chính: {yt}. Hạn mức gợi ý: {kh.get('han_muc', 0):,} ₫."
    if "merchant" in ql and tm:
        xs = sorted(tm, key=lambda v: -v["p_tb"]); top = xs[0]
        return (f"Merchant rủi ro nhất là **{top['merchant_id']}** với P trung bình **{top['p_tb']*100:.2f} %**, tỷ lệ High **{top['high']*100:.1f} %** trên {top['so']} giao dịch. "
                + "Xếp hạng theo P: " + ", ".join(f"{v['merchant_id']} {v['p_tb']*100:.2f} %" for v in xs) + ". Gợi ý: siết hạn mức hoặc đàm phán phí MDR cao hơn với merchant đứng đầu.")
    if re.search(r"tầng|tang|low|medium|high|so sánh", ql) and tt:
        return "So sánh theo tầng: " + "; ".join(f"**{v['tier']}** {v['so']} GD, P TB **{v['p_tb']*100:.2f} %**, duyệt {(v['duyet'] or 0)*100:.0f} %" for v in tt) + ". Khoảng cách P giữa Low và High cho thấy mô hình phân tách tốt."
    if re.search(r"trần|tran|3%|3 %", ql):
        return chung + " Cần chạy phân tích độ nhạy MILP với cùng lô dữ liệu để định lượng tác động của mức trần 3%."
    if re.search(r"top|liệt kê|danh sách|rủi ro nhất", ql):
        return "Dưới đây là 10 giao dịch có P(default) cao nhất trong khoảng đã chọn (bảng bên phải). " + chung
    return "(Chế độ ngoại tuyến – trả lời trực tiếp từ FACTS) " + chung

@app.post("/api/ask")
def ask(req: AskReq, _=Depends(require_private)):
    # Giảm nguy cơ gửi PII do người dùng tự nhập trong câu hỏi tới dịch vụ ngoài.
    clean_question = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[EMAIL_ẨN]", req.question)
    clean_question = re.sub(r"(?<!\d)(?:\+?84|0)[ .-]?(?:\d[ .-]?){9,10}(?!\d)", "[ĐIỆN_THOẠI_ẨN]", clean_question)
    d = tx_in_range(req.d_from, req.d_to); k = kpi_cua(d)
    facts = {"khoang_thoi_gian": [req.d_from, req.d_to], "kpi": k,
             "theo_tang": js(d.groupby("tier").agg(so=("transaction_id", "size"), p_tb=("fpd_prob", "mean"), duyet=("decision", "mean")).reset_index()),
             "theo_merchant": js(d.groupby("merchant_id").agg(so=("transaction_id", "size"), p_tb=("fpd_prob", "mean"), high=("tier", lambda s: (s == "HIGH").mean())).sort_values("p_tb", ascending=False).reset_index()),
             "mo_hinh": {"thick_auc": .79, "thin_auc": .7704, "nguong": {"low": M.low, "high": M.high}, "backtest_no_xau": "2,86 % ± 0,54"}}
    if req.customer_id:
        try: facts["khach"] = js(score(req.customer_id))
        except HTTPException: facts["khach"] = "(không tồn tại)"
    bang, sql_text = None, None
    if not DEMO and re.search(r"\b(bao nhiêu|liệt kê|top|danh sách|nhóm|theo|trung bình|tổng|so sánh|merchant|khách)\b", req.question.lower()):
        try:                                           # text-to-SQL có rào chắn
            cau, _ = LLM_.ask("Bạn là chuyên gia SQLite. " + SQL_GUIDE + " Chỉ trả về câu SQL, không giải thích.", clean_question)
            sql_text = sql_an_toan(cau)
            if sql_text:
                with sqlite3.connect(DB_PATH) as c:
                    c.execute("PRAGMA query_only = 1"); bang = pd.read_sql(sql_text, c)
                facts["ket_qua_truy_van"] = js(bang.head(50))
        except Exception as e: facts["loi_sql"] = str(e)[:200]
    fs = json.dumps(facts, ensure_ascii=False, default=str)
    try:
        text, model_name = LLM_.ask(SYSTEM_PROMPT, f"CÂU HỎI: {clean_question}\nFACTS:\n{fs}")
        if not text: raise RuntimeError("LLM không trả nội dung")
        canh_bao = KIEM_TRA_SO(text, fs); offline = False
    except Exception as e:
        text = tra_loi_ngoai_tuyen(req.question, k, facts, d)
        model_name, canh_bao, offline = f"ngoại tuyến ({type(e).__name__})", [], True
        if re.search(r"top|liệt kê|danh sách|rủi ro nhất", req.question.lower()) and bang is None:
            bang = d.sort_values("fpd_prob", ascending=False).head(10)[["transaction_id", "customer_id", "merchant_id", "amount", "fpd_prob", "tier"]]
    return js({"text": text, "model": model_name, "canh_bao": canh_bao, "offline": offline, "sql": sql_text, "bang": bang, "facts_keys": list(facts)})

# ---------------------------------------------------------------- Agentic RAG (orchestrator + 5 công cụ)
from agent_rag import AgentOrchestrator
AGENT = AgentOrchestrator(M=M, LLM_=LLM_, GUARD=GUARD, kiem_tra_so=KIEM_TRA_SO, db_path=DB_PATH, demo=DEMO,
                          tier_code_fn=tier_code, tx_in_range_fn=tx_in_range, kpi_cua_fn=kpi_cua, sql_guard=sql_an_toan)

@app.post("/api/agent")
def agent(req: AgentReq, _=Depends(require_private)):
    """Luồng Agentic: phân loại ý định -> gọi công cụ (rag/score/policy/milp/sql) -> LLM chỉ diễn giải FACTS."""
    try:
        return js(AGENT.run(req.question, req.d_from, req.d_to, req.customer_id, req.confirm))
    except Exception as e:
        raise HTTPException(500, f"Agent lỗi: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- import dữ liệu
@app.post("/api/upload")
async def upload(file: UploadFile = File(...), kind: str = Query("applications"), _=Depends(require_private)):
    if kind not in {"applications", "transactions"}: raise HTTPException(400, "kind không hợp lệ")
    if not file.filename or not file.filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(400, "Chỉ hỗ trợ .csv và .xlsx")
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024: raise HTTPException(413, "Tệp phải nhỏ hơn hoặc bằng 5 MB")
    try: df = pd.read_csv(io.BytesIO(raw)) if file.filename.lower().endswith(".csv") else pd.read_excel(io.BytesIO(raw))
    except Exception as e: raise HTTPException(400, f"Không đọc được tệp: {e}")
    if df.empty: raise HTTPException(400, "Tệp không có dòng dữ liệu")
    if len(df) > 500: raise HTTPException(400, "Tối đa 500 hồ sơ/giao dịch mỗi lần")
    if kind == "applications":                       # lô hồ sơ mới -> chấm điểm (router thick/thin)
        out = []
        for i, r in df.head(500).iterrows():
            form = {k: (None if pd.isna(v) else v) for k, v in r.to_dict().items()}
            try:
                s = M.score_new(form); out.append({"row": int(i), "p": s["p"], "tier": tier_code(s["tier"]), "model_used": s["model_used"], "han_muc": s.get("han_muc_goi_y")})
            except Exception as e: out.append({"row": int(i), "loi": str(e)[:120]})
        res = pd.DataFrame(out)
        return js({"kind": kind, "n": int(len(df)), "da_cham": int(res.get("p", pd.Series(dtype=float)).notna().sum()),
                   "tom_tat": res.tier.value_counts().to_dict() if "tier" in res else {}, "rows": res, "cot_thieu": [c for c in ["AMT_INCOME_TOTAL", "AMT_CREDIT", "DAYS_BIRTH", "EXT_SOURCE_2"] if c not in df.columns]})
    elif kind == "transactions":                     # lô giao dịch -> ghép điểm sẵn -> MILP
        need = {"customer_id", "amount", "merchant_id"}
        if not need <= set(df.columns): raise HTTPException(400, f"Thiếu cột {need - set(df.columns)}")
        if DEMO: raise HTTPException(400, "DEMO: không có CUSTOMER_SCORE để ghép")
        sc = sql("SELECT customer_id, fpd_probability fpd_prob, risk_tier FROM CUSTOMER_SCORE")
        d = df.merge(sc, on="customer_id", how="left")
        thieu = int(d.fpd_prob.isna().sum()); d = d.dropna(subset=["fpd_prob"]).reset_index(drop=True)
        if "transaction_id" not in d: d["transaction_id"] = [f"UP{i:06d}" for i in range(len(d))]
        d["fee_rate"] = d.merchant_id.map(getattr(__import__("model"), "FEE_MAP")).fillna(0.04); d["target_default"] = np.nan; d["model_used"] = "thick"
        if "proposed_limit" not in d: d["proposed_limit"] = d.amount
        if d.empty: raise HTTPException(400, "Không có giao dịch ghép được điểm mô hình")
        dfo, kq = M.optimize(d=d); run_id = uuid.uuid4().hex[:8]; RUNS[run_id] = dfo
        return js({"kind": kind, "n": int(len(df)), "khong_co_diem": thieu, "run_id": run_id, "kq": kq, "rows": dfo.head(500)})
    raise HTTPException(400, "kind phải là applications | transactions")

@app.get("/api/sample_csv")
def sample_csv(kind: str = "applications", download: int = 0):
    if kind == "transactions":
        txt = "customer_id,amount,merchant_id\n243023,1000000,GRAB\n100002,2500000,SHOPEE\n100003,800000,HIGHLANDS\n"
    else:
        txt = ("NAME_CONTRACT_TYPE,AMT_INCOME_TOTAL,AMT_CREDIT,AMT_ANNUITY,AMT_GOODS_PRICE,DAYS_BIRTH,DAYS_EMPLOYED,EXT_SOURCE_1,EXT_SOURCE_2,EXT_SOURCE_3,"
               "NAME_EDUCATION_TYPE,NAME_FAMILY_STATUS,NAME_HOUSING_TYPE,OCCUPATION_TYPE,ORGANIZATION_TYPE,REGION_RATING_CLIENT,CNT_CHILDREN,CNT_FAM_MEMBERS,FLAG_OWN_CAR,FLAG_OWN_REALTY\n"
               "Cash loans,180000,450000,25000,400000,-12000,-1500,,0.72,0.65,Higher education,Married,House / apartment,Core staff,Business Entity Type 3,2,1,3,N,Y\n"
               "Cash loans,90000,600000,32000,540000,-8500,-400,,0.25,0.2,Secondary / secondary special,Single / not married,Rented apartment,Laborers,Self-employed,3,0,1,N,N\n")
    if download: return Response(txt, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="mau_{kind}.csv"'})
    return JSONResponse({"filename": f"mau_{kind}.csv", "content": txt})

# ---------------------------------------------------------------- web tĩnh (React build)
if os.path.isdir(WEB_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(WEB_DIR, "assets")), name="assets")
    if os.path.isdir(HINH_DIR): app.mount("/hinh", StaticFiles(directory=HINH_DIR), name="hinh")
    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # SPA fallback; không cho đọc source Python hoặc tệp bên ngoài web_build.
        root = Path(WEB_DIR).resolve()
        target = (root / full_path).resolve()
        if target.is_relative_to(root) and target.is_file() and target.suffix in {".html", ".js", ".css", ".svg", ".png", ".ico"}:
            return FileResponse(target)
        return FileResponse(root / "index.html")
