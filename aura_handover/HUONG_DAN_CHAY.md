# CHẠY DASHBOARD AURA

## A. Trên Colab (demo trước hội đồng)
```python
# Cell 1 – chuẩn bị
from google.colab import drive; drive.mount('/content/drive')
!pip -q install streamlit plotly pulp shap lightgbm google-genai pyngrok
%cd "/content/drive/MyDrive/Colab Notebooks/aura_handover"
import os; os.environ["GEMINI_API_KEY"] = "…"            # hoặc dùng Colab Secrets
!python test_lo_i.py                                     # phải in ✅ LÕI SẴN SÀNG BÀN GIAO

# Cell 2 – chạy app + tunnel
from pyngrok import ngrok; ngrok.set_auth_token("TOKEN_NGROK_FREE")
!nohup streamlit run app.py --server.port 8501 --server.headless true > st.log 2>&1 &
import time; time.sleep(5); print(ngrok.connect(8501))
```
(Thay ngrok bằng `!npx localtunnel --port 8501` nếu không có tài khoản ngrok.)

## B. Máy cá nhân
```bash
pip install -r requirements.txt
set AURA_BASE=D:/aura/          # thư mục chứa fpd_model_v1/, fpd_model_thin/, aura_bnpl.db, hinh/
streamlit run app.py
```

## C. Xem giao diện không cần dữ liệu (DEMO)
```bash
AURA_DEMO=1 streamlit run app.py
```
Banner vàng "DEMO – dữ liệu giả lập" sẽ hiện; số liệu là giả, chỉ để xem bố cục.

## Kịch bản demo 3 phút
1. Tab Tổng quan – đọc 6 KPI, chỉ hình flow.
2. Tab Thẩm định – customer 243023 (P ≈ 59,6 %, High) → bấm Giải thích AI → chuyển sang form khách mới → badge Thin-file.
3. Tab Phân bổ vốn – chạy mặc định (660 đơn, 43,04 triệu) → kéo trần xuống 2 % → 408 đơn → mở độ nhạy → Lưu nhật ký.
4. Tab Nhật ký – lọc batch vừa lưu, mục PDPA.

---

## C. Giao diện mới (React + FastAPI) – khuyến nghị dùng để demo

Cấu trúc: `api.py` (FastAPI, bọc `FPDModel` + LLM + SQLite) phục vụ luôn bản build React trong `web_build/`.
Không cần cài Node trên Colab – chỉ cần thư mục `web_build/` đã build sẵn.

### C1. Chạy trên Colab (lõi thật)
```python
!pip -q install fastapi uvicorn python-multipart pyngrok PuLP lightgbm shap google-genai
import os, subprocess, time
os.environ["AURA_BASE"] = "/content/drive/MyDrive/Colab Notebooks/"   # nơi có aura_bnpl.db, fpd_model_v1/, baseline_comparison.csv, fairness.csv
os.environ["GEMINI_API_KEY"] = "..."                                   # bỏ qua nếu muốn chế độ ngoại tuyến
%cd "/content/drive/MyDrive/Colab Notebooks/aura_handover"
p = subprocess.Popen(["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]); time.sleep(8)
from pyngrok import ngrok; ngrok.set_auth_token("TOKEN_NGROK"); print(ngrok.connect(8000))
```
Mở link ngrok → giao diện. Kiểm tra `…/api/health` phải trả `"demo": false`.

### C2. Chạy máy cá nhân (demo không cần model)
```bash
pip install fastapi uvicorn python-multipart pandas numpy
AURA_DEMO=1 uvicorn api:app --host 0.0.0.0 --port 8000      # Windows: set AURA_DEMO=1 && uvicorn ...
```

### C3. Sửa giao diện (chỉ khi cần)
```bash
cd web && npm install && npm run dev        # dev server 5173, proxy /api -> 8010
npm run build                               # xuất ra ../web_build/
```

### C4. Trang & endpoint
| Trang | Endpoint |
|---|---|
| Tổng quan, Danh mục rủi ro | `GET /api/summary?d_from&d_to`, `GET /api/transactions` |
| Thẩm định hồ sơ | `GET /api/score/{id}`, `POST /api/score_new` |
| Tối ưu vốn | `POST /api/optimize`, `POST /api/sensitivity`, `POST /api/log` |
| Đánh giá mô hình | `GET /api/evaluation` (đọc `baseline_comparison.csv`, `fairness.csv`) |
| Nhật ký & Đạo đức | `GET /api/decision_log`, `GET /api/pii_audit` |
| Trợ lý AI | `POST /api/ask` (facts + text-to-SQL chỉ-đọc; không key → trả lời ngoại tuyến) |
| Nhập dữ liệu | `POST /api/upload?kind=applications|transactions`, `GET /api/sample_csv` |

### C5. Chạy lõi thật trên máy cá nhân (tải mô hình từ Drive)
1. Trên Drive, chia sẻ thư mục chứa `fpd_model_v1/`, `aura_bnpl.db`, `baseline_comparison.csv`, `fairness.csv` ở chế độ **Anyone with the link – Viewer**, copy link.
2. Trong thư mục `aura_handover`:
   ```bash
   pip install -r requirements.txt
   python tai_mo_hinh.py "<link thư mục Drive>"        # tải về ./du_lieu/
   ```
3. Chạy với lõi thật:
   - PowerShell: `$env:AURA_BASE="$PWD\du_lieu\"; python -m uvicorn api:app --port 8000`
   - Mac/Linux: `AURA_BASE=$PWD/du_lieu/ uvicorn api:app --port 8000`
4. Mở http://localhost:8000 — banner vàng DEMO phải biến mất; `/api/health` trả `"demo": false`.
   Muốn có chatbot Gemini: đặt thêm `GEMINI_API_KEY` trước khi chạy (không có key → trợ lý trả lời ngoại tuyến từ FACTS, vẫn dùng được).

### C6. Dọn thư mục trước khi nộp
`python don_dep.py` (xoá node_modules, __pycache__). Thư mục nộp gồm: `api.py model.py features.py llm.py demo_core.py web_build/ web/ requirements.txt tai_mo_hinh.py HUONG_DAN_CHAY.md hinh/`.

### C7. Chế độ Agent (Agentic RAG) – đã tích hợp sẵn
Trợ lý ở trang **Trợ lý** có nút bật/tắt **Agent: BẬT/TẮT**. Khi bật, câu hỏi được Orchestrator
(`agent_rag.py`) xử lý theo luồng: phân loại ý định → gọi công cụ → LLM chỉ diễn giải FACTS:
- `rag_search` – tra cứu corpus tài liệu Phase 2 trong `rag_corpus/` (thêm/sửa file .md tại đó là có tác dụng ngay khi khởi động lại).
- `score_customer` + `apply_policy_rules` – chấm điểm và đối chiếu ngưỡng cho câu hỏi về một khách (mã 6 số).
- `run_milp` – chạy tối ưu; CHỈ ghi nhật ký quyết định khi request có `confirm: true` (nút giao diện mặc định KHÔNG ghi).
- `query_sql` – chỉ SELECT có rào chắn (bảng trong danh mục, LIMIT ≤ 200).
Câu hỏi ngoài phạm vi (ví dụ bitcoin, đầu tư) bị từ chối ngay, không gọi LLM. API tương ứng: `POST /api/agent`.
Kiểm thử: `pytest tests/test_agent_demo.py` (7 test) hoặc chạy cả bộ `pytest tests/` (16 test).
