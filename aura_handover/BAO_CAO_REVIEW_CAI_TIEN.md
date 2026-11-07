# AURA-DSS — Rà soát source & bàn giao bản cải thiện

Ngày rà soát: 14/10/2026. Phạm vi: `aura_handover.zip`, gồm backend `api.py`, Streamlit cũ `app.py`, lõi ML/MILP `model.py`, dữ liệu DEMO, giao diện React (`web/src`) và React bundle (`web_build`).

## 1. Kết luận

- **Nền tảng để demo tốt:** 8 trang React và 10+ API nghiệp vụ bao phủ tổng quan, phân tầng rủi ro, thẩm định, phân bổ vốn, sensitivity, trợ lý, đánh giá, nhật ký, import.
- **Mới xác nhận luồng DEMO:** archive KHÔNG chứa `aura_bnpl.db`, `fpd_model_v1/`, `fpd_model_thin/`, `baseline_comparison.csv`, `fairness.csv` nên chưa thể xác nhận độ chính xác, solver CBC hay latency trên lõi thật.
- **Trọng tâm sửa:** tính chính xác của ngữ nghĩa nghiệp vụ/hậu kiểm, fallback AI, ràng buộc đầu vào, bảo vệ API và demo ổn định.
- **Không khẳng định:** tuân thủ PDPA đầy đủ, fairness đạt chuẩn, hiệu quả kinh tế thực tế hay production-readiness.

## 2. Kết quả đánh giá theo thành phần

| Mục | Đánh giá sau rà soát | Điều kiện nghiệm thu tiếp |
|---|---|---|
| UI/UX React | Mạnh: tổng quan nhiều KPI, có tương tác, nhóm chức năng rõ. Đã bổ sung nguồn dữ liệu và responsive trong mã nguồn. | Build React, chụp ảnh/kiểm tra màn hình 1366×768, 1920×1080 và mobile. |
| Phân tích mô tả | Các tuyến `/summary`, `/transactions` chạy với DEMO. | Đối soát số liệu với SQLite thật và SQL chương 3. |
| LightGBM Thin/Thick | API được thiết kế nối sang `FPDModel`, chưa có artifact để kiểm tra. | Gửi model/meta/data; so sánh 10 khách với notebook. |
| SHAP | Màn hình giải thích có cấu trúc tốt. | Kiểm tra SHAP thật và đối chiếu tên feature/giải thích với model. |
| Tối ưu MILP | API và What-If có cấu trúc, DEMO **là greedy heuristic**, không phải MILP. | Dùng PuLP/CBC thật; xác nhận solver status `Optimal`, ràng buộc vốn/rủi ro và KPI. |
| Chatbot GenAI | Có FACTS, cơ chế text-to-SQL và fallback; đã sửa tình huống text rỗng. | Cấu hình Gemini, thử 10 câu hỏi và 5 prompt injection/PII cases. |
| Audit/PDPA | Có masking và danh sách audit trong RAM. | Phân quyền, lưu vết lâu dài, kiểm tra quy định pháp lý/hạn lưu dữ liệu trước sử dụng thực tế. |

## 3. Những thay đổi đã thực hiện

1. `api.py`: chuyển đường dẫn sang `Path`, hỗ trợ `AURA_BASE` có hoặc không có dấu `/` cuối; thông tin provenance `/api/health`.
2. `api.py`: giới hạn tham số solver, ngày tháng, paging, file CSV/XLSX <= 5 MB / 500 dòng; báo lỗi 422/400 rõ ràng.
3. `api.py`: API tùy chọn yêu cầu `AURA_ACCESS_TOKEN` khi chia sẻ tunnel; bỏ CORS wildcard.
4. `api.py`: tra cứu giao dịch ẩn `target_default` theo bản ghi (vẫn giữ trong phép hậu kiểm tổng hợp). Ngăn log cùng `run_id` hai lần.
5. `api.py`: sửa fallback khi Gemini trả về `None`; lọc email/số điện thoại trực tiếp trong câu hỏi trước khi gửi mô hình ngoài.
6. `api.py`: làm chặt SQL read-only, kiểm soát giới hạn kết quả, bỏ phép tìm kiếm regex ở ô tra cứu ID, xử lý thời gian và tập giao dịch rỗng.
7. `model.py`: không tự nhận **nợ xấu hậu kiểm bằng 0** khi upload giao dịch không có nhãn TARGET; không gắn nhãn `Optimal` nếu CBC không chứng minh nghiệm tối ưu (tránh ghi quyết định không hợp lệ).
8. `demo_core.py`: sửa hạn mức DEMO tối đa 5.000.000 đồng; đặt trạng thái DEMO là `Heuristic`, không giả làm MILP.
9. `web/src/`: nguồn dữ liệu/tính chất mô phỏng được ghi rõ; đổi các nhãn chưa chính xác về tín dụng, thêm giao diện nhập mã truy cập API, responsive và cải thiện khả năng điều hướng bằng bàn phím.
10. `web_build/`: cập nhật các nhãn quan trọng trong bundle cũ và thêm dải provenance cho bản demo chạy ngay mà không cần Node.
11. `tests/test_api_demo.py`: thêm smoke tests cho APIs, điều kiện biên, import, fallback, ghi log trùng, rào chắn SQL.

## 4. Điểm phải chốt với nhóm trước viết chương 5–7

### A. Bất nhất Thin-file 82 vs 86
- Báo cáo Chương 3–4 đề cập **86 đặc trưng Thin-file**.
- Hướng dẫn cũ, API gốc và phần giao diện ghi **82 đặc trưng**.
- Source đã ưu tiên hiển thị số đặc trưng của `meta_thin` khi thực sự có model. **Chưa thể chốt số đúng** vì ZIP không chứa file `fpd_model_thin/meta.json`. Khi nhận file, đối chiếu `meta_thin['features']`, chuẩn hóa lại báo cáo và UI.

### B. TARGET khác First Payment Default
- Home Credit `TARGET` phản ánh khó khăn thanh toán theo định nghĩa nguồn dữ liệu, **không phải nhãn FPD của giao dịch BNPL**.
- Phải ghi “xác suất rủi ro tín dụng đại diện”, “TARGET lịch sử/Home Credit hậu kiểm”, “BNPL mô phỏng”; không kết luận mô hình FPD đã được kiểm định trên BNPL thực.
- Phí MDR và lợi ích ròng hiện là **mô phỏng/kỳ vọng**, không phải doanh thu nhận được từ vận hành thực tế.

### C. Nguồn KPI Chương 6 và fairness Chương 7
- `/api/evaluation` có `SO_TINH` và dữ liệu **fallback mẫu** nếu không có `baseline_comparison.csv`/`fairness.csv`.
- API đã trả `baseline_source` và `fairness_source` (`csv` / `reference_only`). Khi viết chương 6–7 chỉ dùng chỉ tiêu đã truy xuất notebook/chạy test và được xác minh; tuyệt đối không trình bày sample fallback như kết quả đo mới.

### D. Vấn đề vận hành
- Chưa có đăng nhập, RBAC, rate limiting, truy vấn SQL timeouts hay audit bền vững; không dùng làm hệ thống tín dụng thực.
- Nếu mở tunnel công khai, **bắt buộc** đặt biến `AURA_ACCESS_TOKEN` và không công khai DB/PII, API key. React source mới có ô token; build cũ không có, cần `npm run build` sau khi cài dependencies để dùng chế độ token.
- Không triển khai auto-approve/giải ngân: danh mục MILP là đề xuất chờ phê duyệt.

## 5. Kiểm thử đã chạy

- `AURA_DEMO=1 python -m pytest -q tests/test_api_demo.py` → **6 passed**.
- Các API được smoke-test qua FastAPI TestClient: `/api/health`, `/api/summary`, `/api/transactions`, `/api/score/{id}`, `/api/score_new`, `/api/optimize`, `/api/sensitivity`, `/api/evaluation`, `/api/decision_log`, `/api/ask`, `/api/upload` ở tình huống lỗi.
- Các lỗi ngày đảo, rủi ro/vốn không hợp lệ được chặn; miền dữ liệu trống trả JSON thay vì 500.
- **Chưa chạy** LightGBM thật + PuLP/CBC thật (thiếu artifact dữ liệu), tải Gemini thật (thiếu khóa API) và Vite build mới (môi trường xử lý không tải đầy đủ Node packages). **Không coi frontend rebuild là đã nghiệm thu.**

## 6. Ưu tiên tiếp theo

1. Bổ sung `aura_bnpl.db`, thư mục 2 model (đặc biệt 2 file `meta.json`) và 2 CSV đánh giá.
2. Đối soát hoạt động thật của 8 trang, checkpoint Chương 3–4, chạy baseline/latency và ảnh giao diện làm Chương 5.
3. Thu thập số đo chính thức và định nghĩa mẫu cho Chương 6.
4. Chạy fairness theo nhóm và kiểm chứng PII/audit cho Chương 7.

> Lưu ý phạm vi: đây là bản **cải thiện có kiểm thử DEMO**, không phải chứng nhận độ chính xác ML, nghiệm tối ưu MILP hoặc an toàn dữ liệu trong production.
