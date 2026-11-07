# =====================================================================================
#  agent_rag.py – Tầng Agentic RAG cho AURA-DSS (tích hợp trực tiếp, không thêm phụ thuộc).
#  Kiến trúc: Orchestrator phân loại ý định -> gọi công cụ (tools) -> LLM chỉ diễn giải FACTS.
#  Nguyên tắc bất biến (kế thừa api.py): LLM KHÔNG BAO GIỜ sinh số nghiệp vụ; mọi ghi dữ liệu
#  phải qua cổng xác nhận (confirm=True); PII không bao giờ được nạp vào ngữ cảnh Agent.
#  Công cụ (5):
#    rag_search       – truy xuất tri thức từ rag_corpus/ (BM25 nhẹ, thuần Python)
#    score_customer   – chấm điểm + giải thích một khách (chỉ đọc)
#    apply_policy_rules – bộ quy tắc vi mô: tầng, ngưỡng, hạn mức (chỉ đọc)
#    run_milp         – chạy tối ưu PuLP/CBC; CHỈ công cụ này có khả năng ghi, và chỉ khi confirm=True
#    query_sql        – SELECT có rào chắn (dùng lại sql_an_toan của api.py qua callback)
#  Chạy thử:  pytest tests/test_agent_demo.py   (AURA_DEMO=1, không cần model thật)
# =====================================================================================
import os, re, json, time, sqlite3, math
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

CORPUS_DIR = Path(__file__).resolve().parent / "rag_corpus"

# ---------------------------------------------------------------- che PII trong câu hỏi (đồng bộ api.py)
def mask_pii_question(q: str) -> str:
    """Che email + số điện thoại người dùng tự nhập trước khi đưa vào FACTS/LLM."""
    q = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[EMAIL_ẨN]", q or "")
    q = re.sub(r"(?<!\d)(?:\+?84|0)[ .-]?(?:\d[ .-]?){9,10}(?!\d)", "[ĐIỆN_THOẠI_ẨN]", q)
    return q

# ---------------------------------------------------------------- phạm vi & ý định
OOS_PATTERNS = re.compile(
    r"\b(bitcoin|crypto|tiền ?mã|hóa ?đơn ?điện|chứng khoán|cổ phiếu|forex|đầu tư|lãi suất ngân hàng|"
    r"thời tiết|bóng đá|phim|nhạc|game|chính trị|bầu cử|viết ?thơ|viết ?văn|làm ?bài ?tập|"
    r"số ?cccd|cmnd|số ?thật|họ ?tên ?thật|người ?yêu|tử ?vi|horoscope)\b", re.I)

INTENT_RULES = [  # (intent, regex) – ưu tiên theo thứ tự
    ("ngoai_pham_vi", OOS_PATTERNS),
    ("ho_so",          re.compile(r"\b\d{6}\b|khách ?hàng|khách \w+|hồ ?sơ|shap|yếu ?tố|thẩm ?định|tra ?cứu", re.I)),
    ("toi_uu",         re.compile(r"tối ?ưu|milp|phân ?bổ|phân ?vốn|quỹ|ngân ?sách|trần ?rủi ?ro|lợi ?nhuận|duyệt ?bao ?nhiêu ?đơn", re.I)),
    ("tai_lieu",       re.compile(r"fr-?0?\d|báo ?cáo|tài ?liệu|phase ?2|nghĩa ?vụ|kiến ?trúc|mục ?tiêu|phương ?pháp|chương ?\d|thiết ?kế|hiệu ?năng|p99|công ?bằng|riêng ?tư|nghị ?định|yêu ?cầu ?chức ?năng|hạn ?chế", re.I)),
    ("truy_van",       re.compile(r"bao ?nhiêu|liệt ?kê|top ?\d*|danh ?sách|trung ?bình|tổng|so ?sánh|merchant|giao ?dịch ?nào", re.I)),
]

def phan_loi_y_dinh(q: str) -> str:
    for intent, pat in INTENT_RULES:
        if pat.search(q or ""):
            return intent
    return "tong_hop"

# ---------------------------------------------------------------- corpus RAG
def _tokenize(s: str) -> List[str]:
    return re.findall(r"[a-zà-ỹđ0-9][a-zà-ỹđ0-9\-.]*", (s or "").lower())

def nap_corpus(thu_muc: Path = CORPUS_DIR) -> List[Dict[str, Any]]:
    """Mỗi file .md = 1 chunk; dòng '@tags:' là metadata; tiêu đề lấy từ '# ...'."""
    chunks = []
    for f in sorted(thu_muc.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        tags = []
        lines = []
        for ln in text.splitlines():
            if ln.startswith("@tags:"):
                tags = [t.strip() for t in ln[6:].split(",") if t.strip()]
            else:
                lines.append(ln)
        body = "\n".join(lines).strip()
        m = re.match(r"#\s*(.+)", body)
        chunks.append({"id": f.stem, "title": (m.group(1).strip() if m else f.stem),
                       "tags": tags, "text": body, "tokens": _tokenize(body + " " + " ".join(tags))})
    return chunks

class _BM25Nhe:
    """BM25 rút gọn (k1=1.5, b=0.75) thuần Python – đủ dùng cho corpus < 100 chunk."""
    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.N = len(chunks) or 1
        self.avgdl = (sum(len(c["tokens"]) for c in chunks) / self.N) or 1.0
        self.df: Dict[str, int] = {}
        self.tfs = []
        for c in chunks:
            tf: Dict[str, int] = {}
            for t in c["tokens"]:
                tf[t] = tf.get(t, 0) + 1
            self.tfs.append(tf)
            for t in tf:
                self.df[t] = self.df.get(t, 0) + 1

    def search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        if not self.chunks:
            return []
        k1, b = 1.5, 0.75
        qts = _tokenize(query)
        kq = []
        for i, c in enumerate(self.chunks):
            tf, dl = self.tfs[i], max(len(c["tokens"]), 1)
            s = 0.0
            for t in qts:
                if t not in tf:
                    continue
                idf = math.log(1 + (self.N - self.df.get(t, 0) + 0.5) / (self.df.get(t, 0) + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / self.avgdl))
            # thưởng cụm khớp nguyên câu (trích dẫn/từ khoá dài)
            if len(query) > 12 and query.lower() in c["text"].lower():
                s += 3.0
            if s > 0:
                kq.append({"id": c["id"], "title": c["title"], "score": round(s, 3),
                           "tags": c["tags"], "text": c["text"][:1200]})
        return sorted(kq, key=lambda x: -x["score"])[:max(1, k)]

# ---------------------------------------------------------------- Orchestrator
AGENT_SYSTEM = ("Bạn là trợ lý Agentic của hệ hỗ trợ ra quyết định tín dụng BNPL AURA. Bạn được cung cấp TRACE (các bước công cụ đã chạy) "
                "và FACTS (số liệu do công cụ trả về). Quy tắc: CHỈ dùng số liệu có trong FACTS và trích dẫn trong NGUỒN; nếu thiếu, ghi "
                "'(không có số liệu)'. Khi FACTS có nguồn (nguon_rag), nêu tên tài liệu được trích. Trả lời tiếng Việt, ngắn gọn (≤ 150 từ), "
                "kết thúc bằng 1 khuyến nghị hành động. Không tự sinh số nghiệp vụ, không thay tầng rủi ro/xác suất/quyết định đã có.")

class AgentOrchestrator:
    """Orchestrator Agentic RAG – nhận dependency từ api.py, không import ngược api.py."""

    def __init__(self, M, LLM_, GUARD, kiem_tra_so: Callable, db_path: str, demo: bool,
                 tier_code_fn: Callable, tx_in_range_fn: Callable, kpi_cua_fn: Callable,
                 sql_guard: Callable, corpus_dir: Path = CORPUS_DIR):
        self.M, self.LLM_, self.GUARD, self.kiem_tra_so = M, LLM_, GUARD, kiem_tra_so
        self.db_path, self.demo, self.tier_code = db_path, demo, tier_code_fn
        self.tx_in_range, self.kpi_cua, self.sql_guard = tx_in_range_fn, kpi_cua_fn, sql_guard
        self.index = _BM25Nhe(nap_corpus(corpus_dir))

    # ---------- tiện ích trace ----------
    @staticmethod
    def _step(trace, tool, ten, chi_tiet, t0, trang_thai="ok"):
        trace.append({"tool": tool, "ten": ten, "chi_tiet": str(chi_tiet)[:300],
                      "ms": int((time.perf_counter() - t0) * 1000), "trang_thai": trang_thai})

    # ---------- 5 công cụ ----------
    def tool_rag_search(self, query: str, k: int = 4):
        hits = self.index.search(query, k=k)
        return hits, [ {"id": h["id"], "title": h["title"], "score": h["score"]} for h in hits ]

    def tool_score_customer(self, cid: int):
        s = self.M.score_customer(cid)                     # KeyError -> caller bắt
        ex = self.M.explain(cid)
        han_muc = self.M.han_muc(s["p"], s.get("model_used", "thick"))
        # PII không được nạp vào ngữ cảnh Agent (FR-07) – kể cả khi người dùng hỏi khách cụ thể.
        return {"customer_id": cid, "p": s["p"], "tier": s["tier"], "tier_code": self.tier_code(s["tier"]),
                "model_used": s.get("model_used", "thick"), "han_muc": han_muc, "explain": ex}

    def tool_policy_rules(self, p: Optional[float] = None, model_used: str = "thick"):
        """Bộ quy tắc vi mô (chỉ đọc): ngưỡng tầng từ meta + quy tắc hạn mức."""
        quy_tac = {"nguong": {"low": self.M.low, "high": self.M.high},
                   "tang": list(getattr(self.M, "labels", ["1. LOW", "2. MEDIUM", "3. HIGH"])),
                   "mdr_map": getattr(__import__("model"), "FEE_MAP", {}) if not self.demo else {"SHOPEE": 0.045, "GRAB": 0.035},
                   "ghi_chu": "Ngưỡng đọc từ meta.json; MILP chỉ ghi khi người dùng xác nhận."}
        if p is not None:
            quy_tac["ap_dung"] = {"p": p, "tier": self.M.tier(p), "han_muc_goi_y": self.M.han_muc(p, model_used)}
        return quy_tac

    def tool_run_milp(self, liquidity=2e9, risk_ceiling=0.04, lgd=0.6, n=1000, seed=42,
                      d_from=None, d_to=None, confirm: bool = False):
        """Công cụ DUY NHẤT có khả năng ghi (FACT_DECISION_LOG) – chỉ khi confirm=True."""
        d = None
        if d_from or d_to:
            base = self.tx_in_range(d_from, d_to)
            if len(base) == 0:
                raise ValueError("Không có giao dịch trong khoảng thời gian đã chọn")
            d = base.sample(n=min(int(n), len(base)), random_state=int(seed)).reset_index(drop=True)
            if "model_used" not in d or d.model_used.isna().all():
                d["model_used"] = "thick"
        df, kq = self.M.optimize(liquidity=liquidity, risk_ceiling=risk_ceiling, lgd=lgd,
                                 n=int(n), seed=int(seed), d=d)
        batch_id = None
        if confirm:                                        # cổng xác nhận: ghi nhật ký quyết định
            batch_id = self.M.log_decisions(df, None)
        return {"kq": kq, "batch_id": batch_id, "ghi_nhat_ky": bool(confirm),
                "tham_so": {"liquidity": liquidity, "risk_ceiling": risk_ceiling, "lgd": lgd, "n": int(n), "seed": int(seed)}}

    def tool_query_sql(self, cau: str):
        q = self.sql_guard(cau)
        if not q:
            return None, "Câu SQL bị từ chối bởi rào chắn (chỉ SELECT, bảng trong danh mục, LIMIT ≤ 200)"
        with sqlite3.connect(self.db_path) as c:
            c.execute("PRAGMA query_only = 1")
            bang = __import__("pandas").read_sql(q, c)
        return q, bang

    # ---------- lời mẫu ngoại tuyến theo ý định ----------
    def _fallback(self, intent, q, facts) -> str:
        k = facts.get("kpi", {})
        fmtp = lambda v, dp=2: (f"{v*100:.{dp}f} %" if isinstance(v, (int, float)) else "chưa có số liệu")
        chung = (f"Kỳ đã chọn có **{k.get('so_giao_dich', '(không có số liệu)')}** giao dịch, P trung bình **{fmtp(k.get('p_tb'))}**, "
                 f"tỷ lệ High **{fmtp(k.get('ty_le_high'), 1)}**, tỷ lệ đề xuất **{fmtp(k.get('ty_le_duyet'), 1)}**.")
        if intent == "ho_so" and isinstance(facts.get("khach"), dict):
            kh = facts["khach"]; ex = kh.get("explain", {})
            yt = ", ".join(x.get("ten", "?") for x in ex.get("tang_rui_ro", [])[:3]) or "(không có số liệu)"
            return (f"Khách **{kh['customer_id']}** có P(default) **{kh['p']*100:.1f} %** → tầng **{kh['tier_code']}** ({kh['model_used']}-file). "
                    f"Yếu tố tăng rủi ro chính: {yt}. Hạn mức gợi ý: {kh.get('han_muc', 0):,} ₫. Khuyến nghị: kiểm tra bằng chứng trước khi phê duyệt.")
        if intent == "toi_uu" and isinstance(facts.get("milp"), dict):
            kq = facts["milp"].get("kq", {})
            return ("Kết quả MILP (chỉ tính toán, chưa ghi nhật ký): " + chung +
                    f" Số đơn đề xuất duyệt **{kq.get('so_don_duyet', '(không có số liệu)')}**, sử dụng vốn **{fmtp(kq.get('su_dung_von'),1)}**, "
                    f"nợ xấu dự đoán **{fmtp(kq.get('no_xau_du_doan'))}**. Khuyến nghị: mở trang Tối ưu vốn để xem chi tiết và bấm ghi nhật ký nếu chấp nhận phương án.")
        if intent == "tai_lieu" and facts.get("nguon_rag"):
            ten = "; ".join(v["title"] for v in facts["nguon_rag"][:2])
            return f"(Chế độ ngoại tuyến) Câu hỏi thuộc tài liệu Phase 2. Nguồn khớp nhất: {ten}. " + chung + " Khuyến nghị: đọc trực tiếp phần trích dẫn trong bảng nguồn."
        if intent == "truy_van" and isinstance(facts.get("ket_qua_truy_van"), list):
            n = len(facts["ket_qua_truy_van"])
            return f"(Chế độ ngoại tuyến) Truy vấn trả về **{n}** dòng (xem bảng bằng chứng). " + chung + " Khuyến nghị: đối chiếu bảng trước khi kết luận."
        return "(Chế độ ngoại tuyến – trả lời trực tiếp từ FACTS) " + chung + " Khuyến nghị: chạy lại khi có kết nối Gemini để nhận phân tích đầy đủ."

    # ---------- luồng chính ----------
    def run(self, question: str, d_from: Optional[str] = None, d_to: Optional[str] = None,
            customer_id: Optional[int] = None, confirm: bool = False) -> Dict[str, Any]:
        t_all = time.perf_counter()
        trace: List[Dict[str, Any]] = []
        q = mask_pii_question((question or "").strip())
        facts: Dict[str, Any] = {"cau_hoi": q, "khoang_thoi_gian": [d_from, d_to]}

        # 1) Phân loại ý định
        t0 = time.perf_counter(); intent = phan_loi_y_dinh(q)
        if customer_id:                                     # người dùng chỉ định mã khách -> ép ý định
            intent = "ho_so"
        self._step(trace, "phan_loi", "Phân loại ý định", f"intent={intent}", t0)

        # 2) Ngoài phạm vi -> từ chối, không gọi LLM
        if intent == "ngoai_pham_vi":
            self._step(trace, "bao_ve", "Rào chắn phạm vi", "Từ chối câu hỏi ngoài phạm vi tín dụng BNPL của AURA", t_all, "tu_choi")
            return {"text": "Câu hỏi này ngoài phạm vi của AURA-DSS. Trợ lý chỉ xử lý: chấm điểm hồ sơ BNPL, phân tầng rủi ro, "
                            "tối ưu phân bổ vốn (MILP), KPI danh mục và tài liệu thiết kế Phase 2 của nhóm.",
                    "model": "Rào chắn phạm vi", "intent": intent, "trace": trace, "facts_keys": list(facts),
                    "canh_bao": [], "offline": False, "bang": None, "sql": None, "run_id": None, "nguon_rag": []}

        # 3) KPI danh mục luôn có trong FACTS
        try:
            t0 = time.perf_counter()
            d = self.tx_in_range(d_from, d_to)
            facts["kpi"] = self.kpi_cua(d)
            facts["mo_hinh"] = {"thick_auc": 0.79, "thin_auc": 0.7704, "nguong": {"low": self.M.low, "high": self.M.high},
                                "backtest_no_xau": "2,86 % ± 0,54"}
            self._step(trace, "kpi_danh_muc", "Đọc KPI danh mục", f"{int(len(d))} giao dịch trong kỳ", t0)
        except Exception as e:
            self._step(trace, "kpi_danh_muc", "Đọc KPI danh mục", f"Lỗi: {e}", t_all, "loi")

        # 4) Gọi công cụ theo ý định
        bang, sql_text, run_id, nguon_rag = None, None, None, []
        try:
            if intent == "ho_so":
                cid = customer_id or int(re.search(r"\b(\d{6})\b", q).group(1))
                t0 = time.perf_counter()
                facts["khach"] = self.tool_score_customer(cid)
                self._step(trace, "score_customer", f"Chấm điểm khách {cid}",
                           f"P={facts['khach']['p']:.4f}, tầng {facts['khach']['tier_code']}", t0)
                t0 = time.perf_counter()
                facts["quy_tac"] = self.tool_policy_rules(facts["khach"]["p"], facts["khach"]["model_used"])
                self._step(trace, "policy_rules", "Đối chiếu bộ quy tắc", f"tier theo ngưỡng {facts['quy_tac']['nguong']}", t0)
                hits, nguon_rag = self.tool_rag_search(f"giải thích quyết định shap yếu tố rủi ro fr-06")
                facts["nguon_rag"] = nguon_rag
            elif intent == "toi_uu":
                t0 = time.perf_counter()
                milp = self.tool_run_milp(d_from=d_from, d_to=d_to, confirm=confirm)
                facts["milp"] = {"kq": milp["kq"], "tham_so": milp["tham_so"]}
                run_id = milp.get("batch_id")
                self._step(trace, "run_milp", "Chạy MILP (PuLP/CBC)",
                           f"duyệt {milp['kq'].get('so_don_duyet', '?')} đơn · ghi nhật ký={'CÓ' if confirm else 'KHÔNG'}", t0)
                hits, nguon_rag = self.tool_rag_search("milp tối ưu phân bổ vốn trần rủi ro quỹ baseline")
                facts["nguon_rag"] = nguon_rag
            elif intent == "truy_van" and not self.demo:
                t0 = time.perf_counter()
                try:                                        # text-to-SQL có rào chắn (như /api/ask)
                    cau, _ = self.LLM_.ask("Bạn là chuyên gia SQLite. Viết MỘT câu SELECT cho câu hỏi, LIMIT ≤ 200.", q)
                    sql_text, bang = (self.tool_query_sql(cau) if cau else (None, None))
                    if sql_text:
                        facts["ket_qua_truy_van"] = [dict(r) for r in (bang.head(50).to_dict("records") if bang is not None else [])]
                    self._step(trace, "query_sql", "Truy vấn SQL có rào chắn", sql_text or "SQL bị từ chối", t0, "ok" if sql_text else "tu_choi")
                except Exception as e:
                    self._step(trace, "query_sql", "Truy vấn SQL có rào chắn", f"Lỗi: {e}", t0, "loi")
            elif intent == "tai_lieu" or intent == "tong_hop":
                t0 = time.perf_counter()
                hits, nguon_rag = self.tool_rag_search(q, k=4)
                facts["nguon_rag"] = nguon_rag
                facts["trich_dan"] = [{"tai_lieu": h["title"], "noi_dung": h["text"][:600]} for h in hits]
                self._step(trace, "rag_search", "Truy xuất corpus Phase 2",
                           f"{len(hits)} tài liệu: " + ", ".join(h["id"] for h in hits), t0, "ok" if hits else "rong")
        except KeyError as e:
            self._step(trace, "score_customer", "Chấm điểm khách", f"Không tìm thấy mã: {e}", t_all, "loi")
            return {"text": f"Không tìm thấy khách hàng mã {e} trong dữ liệu. Hãy kiểm tra lại mã 6 số ở trang Thẩm định.",
                    "model": "Orchestrator", "intent": intent, "trace": trace, "facts_keys": list(facts),
                    "canh_bao": [], "offline": False, "bang": None, "sql": None, "run_id": None, "nguon_rag": nguon_rag}
        except Exception as e:
            self._step(trace, "cong_cu", "Công cụ", f"Lỗi: {type(e).__name__}: {e}", t_all, "loi")

        # 5) LLM tổng hợp – CHỈ diễn giải FACTS
        fs = json.dumps(facts, ensure_ascii=False, default=str)
        try:
            text, model_name = self.LLM_.ask(AGENT_SYSTEM, f"CÂU HỎI: {q}\nTRACE: {json.dumps(trace, ensure_ascii=False)}\nFACTS:\n{fs}")
            if not text:
                raise RuntimeError("LLM không trả nội dung")
            canh_bao, offline = self.kiem_tra_so(text, fs), False
        except Exception as e:
            text, model_name, canh_bao, offline = self._fallback(intent, q, facts), f"ngoại tuyến ({type(e).__name__})", [], True

        # 6) Bảng bằng chứng dự phòng cho câu liệt kê khi không có SQL
        if bang is None and re.search(r"top|liệt kê|danh sách|rủi ro nhất", q, re.I) and intent != "ngoai_pham_vi":
            try:
                bang = d.sort_values("fpd_prob", ascending=False).head(10)[["transaction_id", "customer_id", "merchant_id", "amount", "fpd_prob", "tier"]]
            except Exception:
                bang = None

        return {"text": text, "model": model_name, "intent": intent, "trace": trace,
                "facts_keys": list(facts), "canh_bao": canh_bao, "offline": offline,
                "bang": bang, "sql": sql_text, "run_id": run_id, "nguon_rag": nguon_rag,
                "tong_ms": int((time.perf_counter() - t_all) * 1000)}
