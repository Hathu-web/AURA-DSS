# Kiểm tra frontend trước khi đổi giao diện

Nguồn: AURA_DSS_Source_UI_Refined_2026-10-14(1).zip. Bản gốc được giữ riêng; bản sửa được kiểm tra bằng SHA-256 so với các tệp trong ZIP.

## Phạm vi bản duyệt

Theo mục IX của FRONTEND DEVELOPMENT BRIEF: thực hiện Phase 0, Phase 1 và Phase 2; nghiệm thu Tổng quan trước khi triển khai sâu Phase 3–5. Các trang nghiệp vụ dùng chung bộ khung mới. Danh mục nhận liên kết merchant từ Tổng quan để truy vết giao dịch. Không thay đổi backend, API contract, dữ liệu, model hay solver.

## Cấu trúc hiện tại

React, Vite, React Router với HashRouter; ECharts qua echarts-for-react. FastAPI phục vụ thư mục web_build. Biến trạng thái dùng chung giữ bộ lọc thời gian xuyên trang. Khi dùng Vite, proxy kết nối FastAPI ở cổng 8010 theo cấu hình gốc.

| Trang hoặc thành phần | API giữ nguyên | Vai trò |
| --- | --- | --- |
| Nguồn và kỳ dữ liệu | GET /api/health | DEMO/LIVE, ngày giao dịch mới nhất, ngưỡng mô hình |
| Tổng quan, phân tích | GET /api/summary?d_from&d_to | KPI, kỳ trước, merchant, phân tầng, dữ liệu ngày |
| Danh mục | GET /api/transactions | Lọc và sắp xếp giao dịch |
| Thẩm định | GET /api/score/{id}, POST /api/score_new | Điểm rủi ro, Thin/Thick, SHAP |
| Tối ưu | POST /api/optimize, POST /api/sensitivity | Kịch bản, phân bổ, độ nhạy |
| Minh chứng | GET /api/evaluation | So sánh B0–B3, metrics và nguồn dữ liệu |
| Trợ lý | POST /api/ask | Trả lời, SQL/FACTS, fallback |
| Nhập dữ liệu | POST /api/upload, GET /api/sample_csv | Hồ sơ và lô giao dịch |
| Nhật ký | POST /api/log, GET /api/decision_log, GET /api/pii_audit | Ghi và đọc quyết định, kiểm soát dữ liệu |

## Component và tệp dự kiến thay đổi

- App.jsx: Sidebar, PageHeader, DateRangeFilter, hành trình quyết định, chế độ thuyết trình.
- index.css: màu, bố cục, typography, responsive; giữ tương thích các class của trang cũ.
- components/Icon.jsx: biểu tượng vector nội bộ, không tải ảnh hay script ngoài.
- components/executive.jsx: KPI, thẻ biểu đồ, trạng thái lỗi/rỗng và minh chứng B0–B3.
- lib/fmt.js: định dạng vi-VN và chặn tham số chữ số thập phân không hợp lệ.
- lib/overview.js: phép tính trình bày thuần từ phản hồi API, kiểm thử độc lập.
- pages/Overview.jsx: câu chuyện hiện trạng, chênh lệch, merchant, phân tầng và hành động.
- pages/Portfolio.jsx: nhận query merchant khi mở từ Tổng quan; sửa nhãn diễn giải chưa chính xác.
- web_build: bản production build để backend hiện có phục vụ trực tiếp.

## Định nghĩa và rủi ro hồi quy

- p_tb là trung bình xác suất theo giao dịch. no_xau_du_doan_duyet và no_xau_that_duyet là tỷ lệ có trọng số theo số tiền của phần được chọn. Không so sánh chéo hai phạm vi.
- bad ở cấp tầng là trung bình TARGET theo giao dịch; không gọi là tỷ lệ nợ xấu BNPL thực tế hay bằng chứng nhân quả.
- ty_le_duyet và decision được diễn giải là đề xuất chọn, không phải giải ngân thực tế.
- loi_nhuan_that_trieu của backtest là lợi ích ròng hậu kiểm mô phỏng. Không đổi nhãn thành lợi nhuận thực tế hay lợi ích kỳ vọng.
- Kỳ trước chỉ hiển thị khi backend có kỳ đối chiếu với ít nhất một giao dịch. Không tự sinh phần trăm tăng giảm.
- Thí nghiệm B0–B3 độc lập với bộ lọc ngày. Chỉ trình bày như minh chứng khi baseline_source=csv; dữ liệu reference_only được ghi rõ.
- DEMO sử dụng heuristic, không chứng minh CBC tối ưu. ZIP có metadata nhưng không có database và model folds để chạy kiểm thử LIVE.
- Formatter phải chịu được giá trị thiếu, Infinity và tham số thứ hai là object do callback bảng.
- Kiểm tra nhấp merchant, bộ lọc ngày, trạng thái rỗng/lỗi, toàn bộ 8 route, màn hình desktop và điện thoại.


## Điều chỉnh thị giác V2 — 23/10/2026

Thu phản hồi bản trước khác mẫu vì header, thanh mạch truyện và khối cảnh báo quá lớn. V2 chuyển sang bố cục desktop 6 KPI → 3 khối phân tích → 2 khối hành động. Mạch 5 bước chỉ hiện trong chế độ thuyết trình. Thay toàn bộ lớp CSS Phase 1–2 bằng reference.css; giữ CSS thành phần gốc cho các trang hiện hữu. Không thay API, mô hình hoặc dữ liệu backend. Không đưa số liệu minh họa trong ảnh vào KPI thực.


## Bổ sung V3 — 23/10/2026

Sau khi người dùng chấp nhận Tổng quan V2, đã triển khai thiết kế chi tiết bảy trang còn lại. Giữ nguyên byte của `Overview.jsx`, `reference.css`, `App.jsx` từ V2; nạp thêm `pages.css` cho trang chi tiết.

- Source mới: `components/workflow.jsx`, `lib/chartTheme.js`, `lib/workflow.js`, `pages.css`.
- Thiết kế lại: Portfolio, Appraisal, Optimize, Evaluation, Assistant, Ingest, Logs.
- Vẫn dùng nguyên các API summary, transactions, score, score_new, optimize, sensitivity, log, evaluation, ask, upload, decision_log, pii_audit.
- Frontend lưu snapshot tham số tối ưu để chặn ghi kết quả cũ; lưu kỳ của từng câu hỏi AI; xóa kết quả khi đổi hồ sơ/loại upload.
- Xuất CSV escape dấu nháy, dấu phẩy, xuống dòng và chuỗi có thể bị bảng tính diễn giải thành công thức.
- Không tự điền AUC Thin-file khi metadata thiếu; không dùng số tham chiếu tĩnh thay số xác minh.
- Bảng PII audit dùng timestamp/masked hoặc field/at theo phản hồi và không render giá trị nhận diện.
- CSS tăng chữ Tổng quan là tùy chọn tại `web/customize/overview-readable.css`, chưa nạp tự động. Hướng dẫn tại `HUONG_DAN_SUA_CO_CHU.md`.
- Đối chiếu SHA-256 35 file backend/dữ liệu/hỗ trợ gốc không thay đổi. Xem nghiệm thu V3 để biết kiểm thử và giới hạn thực tế.
