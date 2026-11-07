# Chạy bản cải thiện AURA-DSS

## Khởi động nhanh (không có dữ liệu/model)

Trong thư mục gốc dự án:

**Windows PowerShell:**
```powershell
python -m pip install -r requirements.txt
$env:AURA_DEMO="1"
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```
**macOS/Linux:**
```bash
python -m pip install -r requirements.txt
AURA_DEMO=1 python -m uvicorn api:app --host 127.0.0.1 --port 8000
```
Mở `http://127.0.0.1:8000`. `web_build/` đã chứa build React cũ được sửa các nhãn quan trọng và bổ sung cảnh báo nguồn dữ liệu. DEMO sử dụng dữ liệu phát sinh trong `demo_core.py` và heuristic, **không** đại diện kết quả MILP thật.

## Chạy với lõi thật

Chuẩn bị thư mục `DATA_DIR/` chứa:

- `aura_bnpl.db`
- `fpd_model_v1/meta.json`, `fold_0.txt`… và `aux_features.parquet`
- `fpd_model_thin/meta.json`, fold thin-file
- `baseline_comparison.csv`, `fairness.csv` (nếu có, để đánh giá)

PowerShell:
```powershell
Remove-Item Env:\AURA_DEMO -ErrorAction SilentlyContinue
$env:AURA_BASE="D:\data_aura"    # chỉ định thư mục cha chứa các artifact
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```
Xác nhận `http://127.0.0.1:8000/api/health` có `"demo": false`. Nếu là `true`, kiểm tra `reason` (không được lấy số demo làm kết quả báo cáo).

## Sửa giao diện React từ source

```bash
cd web
npm ci
npm run build
cd ..
python -m uvicorn api:app --port 8000
```
React source trong `web/src` có nhiều cải tiến hơn so với bundle được đóng sẵn. `npm run build` cập nhật `web_build/`. Máy thực hiện kiểm thử không lấy được đủ dependency npm nên chưa xác minh lại công đoạn build mới, cần chạy bước này trên máy bạn.

## Chạy test

```bash
python -m pip install pytest httpx
AURA_DEMO=1 python -m pytest -q tests/test_api_demo.py
```
PowerShell dùng `$env:AURA_DEMO="1"` trước câu lệnh test.

## Nếu chia sẻ URL tunnel ra ngoài

Sử dụng HTTPS từ nhà cung cấp tunnel. **Đặt `AURA_ACCESS_TOKEN` trước khi chạy**. API xử lý dữ liệu sẽ trả 401 nếu request thiếu header `X-Aura-Token`. React source mới có trường nhập token trong sidebar; nhớ build lại React để dùng. Nếu chưa build React, chỉ nên chạy local và không chia sẻ link công khai.

Không đưa API key, `.env`, SQLite chứa PII thực hay model artifacts riêng tư vào repo công khai.

## Bổ sung bằng chứng Chương 6–7 (bản tích hợp 14/10/2026)

Trong gói source có sẵn `baseline_comparison.csv`, `fairness.csv` và hai JSON trong `evaluation_artifacts/`. Endpoint `/api/evaluation` dùng chúng cả khi bật `AURA_DEMO=1`; khi đặt `AURA_BASE` ở thư mục khác, endpoint ưu tiên CSV trong `AURA_BASE`, sau đó dùng CSV ở thư mục source. JSON metadata được dùng để chốt 188/86 đặc trưng và P99 102,0 ms, **không thay thế** tệp model `fold_*.txt`.

- Trang Đánh giá hiển thị AUC Thin-file là `Chưa xác minh` vì JSON model Thin không có chỉ số AUC. Biểu đồ ablation và nhóm importance còn là tham chiếu từ phiên bản trước.
- `fairness.csv` chỉ có 977 quan sát với trường giới tính. Không thể khái quát cho toàn bộ 30.000 hồ sơ.
- Đã chỉnh `web/src/pages/Evaluation.jsx` và cập nhật tối thiểu bundle `web_build/assets` cho bản chạy ngay. Muốn nhận đầy đủ cảnh báo theo nhóm và cải tiến UX, cần cài `node_modules` rồi build lại frontend bằng `npm ci && npm run build`.
