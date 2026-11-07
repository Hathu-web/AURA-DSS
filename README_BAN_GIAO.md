# AURA-DSS – Gói bàn giao cho Dashboard & Chatbot

Người nhận: thành viên làm Dashboard / Chatbot. Mục tiêu: **không cần mở notebook** vẫn xây được app.

---

## 1. Checklist file cần copy từ Google Drive (`Colab Notebooks/`)

| File / thư mục | Dung lượng | Dùng để |
|---|---|---|
| `fpd_model_v1/fold_0.txt … fold_4.txt` | 5 × ~3 MB | 5 booster LightGBM (ensemble = trung bình) |
| `fpd_model_v1/meta.json` | nhỏ | **Nguồn sự thật**: tên 188 đặc trưng, danh mục categorical, ngưỡng, tier, metrics, độ trễ |
| `fpd_model_v1/aux_features.parquet` | ~30 MB | Đặc trưng lịch sử (bureau/prev/installments) theo `SK_ID_CURR` – bắt buộc để chấm điểm |
| `fpd_model_v1/feature_importance.csv` | nhỏ | Biểu đồ importance |
| `fpd_model_v1/holdout_predictions.csv` | ~1.5 MB | 61.502 khách holdout (y, p) – vẽ ROC, calibration, lift |
| `fpd_model_v1/shap_values_sample.parquet` | ~7 MB | SHAP 5.000 khách (tùy chọn, cho beeswarm toàn cục) |
| `fpd_model_v1/agent_context_sample.json` | nhỏ | Ví dụ ngữ cảnh đã dựng cho 2 tác tử |
| `aura_bnpl.db` | ~100 MB | SQLite 10 bảng (xem mục 3) |
| `hinh_*.png`, `shap_*.png` | – | Hình tĩnh cho tab Tổng quan nếu cần |
| **Trong gói này**: `features.py`, `model.py`, `llm.py` | – | Code đã tách khỏi notebook |

> **Không được** đổi tên cột / thứ tự cột trong `features.py` – mô hình phụ thuộc chính xác 188 tên trong `meta.json["feature_names"]`.

## 2. Cài đặt & kiểm tra 30 giây

```bash
pip install lightgbm pandas numpy scipy shap pyarrow google-genai streamlit
```
```python
from model import FPDModel
m = FPDModel(model_dir="fpd_model_v1", db_path="aura_bnpl.db")
print(m.score_customer(243023))     # {'p': 0.596, 'tier': '3. High Risk ...', 'source': 'CUSTOMER_SCORE'}
print(m.explain(243023))            # yếu tố tăng/giảm rủi ro (tiếng Việt, định tính) + gợi ý
d, kq = m.optimize(liquidity=2e9, risk_ceiling=0.04); print(kq)
```

## 3. CSDL `aura_bnpl.db` – 10 bảng, khóa `customer_id` (= `SK_ID_CURR` của Home Credit)

```
FACT_BNPL_TRANSACTION (30k)  transaction_id, customer_id, timestamp, amount, merchant_id, proposed_limit
FACT_DECISION_LOG            transaction_id, batch_id, decision(1/0), fpd_probability, risk_tier, fee_amount, decided_at
DIM_CUSTOMER (30k)           customer_id, 43 cột số + 11 cột phân loại + FLAG_DOCUMENT_2..21 (tên gốc Home Credit),
                             income_vnd_month, age_years, years_employed, target_default (nhãn thật – CHỈ để backtest)
DIM_BUREAU_HISTORY (25.7k)   bu_* : lịch sử tín dụng tại TCTD khác (≈ CIC)
DIM_PREVIOUS_LOAN (28.4k)    pv_* : hồ sơ vay trước đây
DIM_REPAYMENT_BEHAVIOR (28.4k) ins_*, ins1y_* : hành vi trả góp (DPD, trả thiếu…)
DIM_WALLET_BEHAVIOR (30k)    MÔ PHỎNG – chỉ minh họa, mô hình không dùng
DIM_CUSTOMER_PII (30k)       full_name, phone_number, device_id, last_gps_location – PHẢI qua PrivacyGuard trước khi hiển thị/gửi LLM
FEATURE_STORE (30k)          customer_id + 188 đặc trưng dạng số (categorical đã mã hóa) – để chấm điểm 3 ms
CUSTOMER_SCORE (30k)         customer_id, fpd_probability, risk_tier, model_version, scored_at
```
Khách không có lịch sử → không có dòng trong 3 bảng DIM_*_HISTORY/LOAN/BEHAVIOR (dùng LEFT JOIN).
Khi đọc **1 dòng** từ SQLite, cột NULL về `None` → luôn dùng `features.ep_kieu_so()` (model.py đã lo).

## 4. Số liệu chốt để hiển thị (từ `meta.json` + backtest)

| Chỉ số | Giá trị |
|---|---|
| Mô hình | LightGBM 5-fold ensemble, 188 đặc trưng, 4 nguồn dữ liệu |
| AUC / Gini / KS (holdout 61.502) | **0.790 / 0.580 / 0.436**, PR-AUC 0.291 |
| Calibration | Decile cuối: dự đoán 30.4% – thật 30.6% (không cần hiệu chỉnh) |
| Ngưỡng theo chi phí (FN:FP = 10:1) | 0.095 → Recall nợ xấu 65%, Precision 20% |
| Tier | Low < 0.048 ≤ Medium < 0.095 ≤ High → bad rate thật 2.4% / 7.1% / 20.1% |
| Độ trễ | Feature store + 5 booster: P99 **3.0 ms**; tra điểm sẵn: 0.3 ms; chấm lô: 1.2 ms/khách |
| Tối ưu vốn (quỹ 2 tỷ, trần 4%, LGD 60%) | Duyệt 66%, nợ xấu dự đoán 3.18%, solver 0.02 s |
| Backtest 20 lô | Nợ xấu thật nhóm duyệt 2.86% ± 0.54 (vs 8.07% duyệt tất cả); nhóm từ chối 16.05% |
| Độ nhạy trần rủi ro | 2%: duyệt 40.8%, LN 35.1 tr · 3%: 63.1%, 42.9 tr · ≥4%: 66%, 43.0 tr (bão hòa) |

## 5. Gợi ý cấu trúc Dashboard (Streamlit) – 4 tab

1. **Tổng quan danh mục** – KPI card (AUC, Gini, KS, bad rate theo tier), phân phối điểm (từ `holdout_predictions.csv`), ROC + calibration, importance top 20, bảng `FACT_DECISION_LOG` theo batch.
2. **Chấm điểm khách hàng** – ô nhập `customer_id` (gợi ý vài ID: 243023 High, chọn thêm từ `CUSTOMER_SCORE` cho Low/Medium) → `score_customer` + `explain` → gauge P, badge tier, 2 cột "yếu tố tăng / giảm rủi ro", lộ trình gợi ý. Tab phụ "Khách mới (form)" → `score_new` (ghi rõ thin-file).
3. **Tối ưu vốn** – slider quỹ vốn (1–3 tỷ), trần rủi ro (2–8%), LGD, Medium cap (30–80%) → `optimize()` → KPI + bảng lô có cột `ly_do` + biểu đồ duyệt theo tier. Nút "Ghi vào FACT_DECISION_LOG".
4. **Chatbot** – 2 chế độ: *Cán bộ tín dụng* (`ANALYST_SYSTEM`, ngữ cảnh = `portfolio_summary()` + `explain(id)` nếu người dùng nhắc ID) và *Khách hàng* (`COACH_SYSTEM`, chỉ ngữ cảnh của 1 khách, qua `PrivacyGuard`). Hiển thị dòng *Nguồn: Gemini (model)* hoặc *Mẫu dự phòng*; chạy `kiem_tra_so()` và hiện cảnh báo nếu có số lạ.

## 6. Quy tắc bắt buộc (đã rút từ các lỗi gặp trong notebook)

- **LLM không quyết định.** Decision/tier/p luôn đến từ `model.py`; LLM chỉ viết lời. Luôn có mẫu dự phòng khi `ask()` trả `None`.
- **PII**: mọi thứ lấy từ `DIM_CUSTOMER_PII` phải qua `PrivacyGuard.sanitize()` trước khi hiển thị hoặc đưa vào prompt.
- **Không hard-code ngưỡng** – đọc `meta.json`.
- **Gemini**: tạo **1 client dùng chung** (tạo inline sẽ lỗi "client has been closed"); đặt timeout; chuỗi model có thể hỏng theo ngày → gọi `LLM.probe_models()` khi cần. Model gọi được ngày 07/10/2026: `gemini-3.5-flash`, `gemini-3-flash-preview`, `gemini-3.5-flash-lite`, `gemini-flash-lite-latest`.
- **Số liệu cho LLM**: đưa đủ con số vào ngữ cảnh; thiếu số → LLM sẽ nội suy (đã xảy ra: "1.39 tỷ" thay vì 1.79 tỷ).
- `accuracy` không được dùng làm KPI (baseline 91.9%); dùng AUC/Gini/KS + chỉ số kinh doanh.
- Quy đổi tiền: `AMT_INCOME_TOTAL` là thu nhập năm ÷ 12 × 1000 = VNĐ/tháng (giả định, ghi rõ trên UI).

## 7. Secrets / cấu hình

- `GEMINI_API_KEY` – Streamlit: `st.secrets["GEMINI_API_KEY"]` hoặc biến môi trường. Không commit key.
- Đường dẫn `MODEL_DIR`, `DB_PATH` đặt trong `config` hoặc biến môi trường.
- Chạy local: `streamlit run app.py`. Trên Colab: `!streamlit run app.py &` + `cloudflared tunnel --url http://localhost:8501`.
