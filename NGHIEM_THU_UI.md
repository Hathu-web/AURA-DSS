# Nghiệm thu giao diện AURA-DSS V3

Ngày 23/10/2026. Phạm vi: giữ nguyên Tổng quan V2 đã duyệt, thiết kế lại bảy trang còn lại; bổ sung hướng dẫn tăng chữ. Backend, dữ liệu và minh chứng gốc giữ nguyên.

## Kết quả

| Hạng mục | Kết quả |
| --- | --- |
| Build production Vite 8.3.4 | Thành công |
| Kiểm thử Node cho formatter, insight, backtest, trạng thái tối ưu và CSV | 15/15 đạt |
| Kiểm thử backend có sẵn: `tests/test_api_demo.py`, `tests/test_evidence_csv.py` | 9/9 đạt với AURA_DEMO=1 |
| Kiểm tra Chromium với backend FastAPI gốc | 54/54 đạt |
| JavaScript pageerror trong các thao tác đã thử | Không ghi nhận |
| SHA-256 đối chiếu ZIP nguồn: 35 tệp ngoài frontend | Không thay đổi |
| So sánh với V2: Overview.jsx, reference.css, App.jsx | Giữ nguyên từng byte |

Chi tiết 54 điểm kiểm tra ở `web/tests/browser_qa_report.json`. Số này bao gồm thao tác, kích thước màn hình và kiểm tra bố cục; không phải 54 kịch bản nghiệp vụ độc lập.

## Các luồng đã thử

| Luồng | Nội dung đã kiểm tra |
| --- | --- |
| Tổng quan | KPI khớp API; đổi kỳ cập nhật KPI và giữ phạm vi backtest độc lập; mở Danh mục đúng merchant và kỳ lọc |
| Danh mục → Thẩm định | Lọc merchant/tầng, mở đúng mã khách hàng; chấm ID và form; thay mã xóa kết quả cũ |
| Tối ưu vốn | Kết quả DEMO ghi đúng solver; đổi tham số đánh dấu kết quả cũ và khóa ghi nhật ký; phân tích độ nhạy với hai trục |
| Tối ưu → Nhật ký | Ghi đề xuất một lần, chuyển đúng batch; số dòng khớp API; lỗi API và thử lại |
| Audit | Fixture theo schema thực tế hiển thị trường/thời điểm; không đưa giá trị nhận diện vào bảng |
| Đánh giá mô hình | AUC Thin thiếu hiện chưa xác minh; số tham chiếu đặt trong phần thu gọn; đổi quỹ và nhóm fairness cập nhật dữ liệu |
| Trợ lý AI | Fallback DEMO; giữ nguyên mã khách hàng; gắn kỳ lọc với từng câu hỏi; mock phản hồi SQL/cảnh báo; bảng cũ giữ đúng câu hỏi; thử lại khi API lỗi |
| Nhập dữ liệu | CSV hồ sơ đi qua API DEMO; số dòng bắt đầu từ 1; đổi loại tệp xóa kết quả cũ; lỗi CUSTOMER_SCORE của lô DEMO được hiện đúng |
| Kiểm tra tệp | Từ chối .xls và tệp trên 5 MB; cho chọn lại CSV hợp lệ |
| Chế độ Thuyết trình | Ẩn sidebar và chuyển bước |

Fixture và mock chỉ nằm trong phiên kiểm tra trình duyệt, không thay đổi API hoặc dữ liệu trong source bàn giao.

## Bố cục và cỡ chữ

- Bảy trang mới không làm root layout tràn ngang ở 1440, 1366 và 390px. Bảng rộng có khung cuộn riêng. Thẩm định và Tối ưu được thử khi đã có kết quả; không khẳng định mọi trạng thái dữ liệu đều đã được thử trên điện thoại.
- Tổng quan V2 vẫn vừa một màn hình ở 1920×900, 1440×900 và 1366×768; root không tràn ngang ở 390px.
- Đã kiểm tra bằng ảnh các trang mới và CSS tăng chữ. Không ghi nhận chữ chồng lên nhau trong những bố cục được xem.
- CSS tùy chọn `web/customize/overview-readable.css` đã thử ở 1440, 1366 và 390px: nội dung Insight lên 12px, thẻ tự giãn và không tràn khung. CSS này **chưa được nạp tự động**; Tổng quan mặc định giữ V2.
- Tăng chữ có thể khiến Tổng quan cần cuộn dọc. Chưa kiểm tra trên máy chiếu thực tế; cần xem lại khi đổi thêm cỡ chữ hoặc thay nội dung dài hơn.

## Phạm vi source

Bảy trang: Portfolio.jsx, Appraisal.jsx, Optimize.jsx, Evaluation.jsx, Assistant.jsx, Ingest.jsx, Logs.jsx. Thành phần dùng chung: components/workflow.jsx, lib/workflow.js, lib/chartTheme.js và pages.css; main.jsx nạp stylesheet. Source, build, kiểm thử frontend và tài liệu bàn giao được cập nhật. API endpoint, schema backend và công thức backend giữ nguyên.

Hướng dẫn chỉnh cỡ chữ: `HUONG_DAN_SUA_CO_CHU.md`. Mạch thuyết trình và vị trí chỉnh từng trang: `HUONG_DAN_UI_STORYTELLING.md`.

## Giới hạn kiểm chứng

- Môi trường chạy AURA_DEMO=1. Chưa xác thực Thin/Thick LIVE, MILP với CBC thật, database LIVE hoặc Gemini trực tuyến. Giao diện ghi rõ solver và nguồn phản hồi thực tế; không coi heuristic DEMO là chứng minh tối ưu toàn cục.
- Lô giao dịch BNPL cần CUSTOMER_SCORE. Đã thử và xác nhận lỗi DEMO được hiển thị; chưa kiểm chứng luồng thành công với database LIVE.
- Chạy toàn bộ pytest bị chặn khi thu thập `test_lo_i.py` do thiếu LightGBM/môi trường mô hình. Con số 9/9 chỉ áp dụng hai tệp kiểm thử nêu trên.
- Lint có 0 lỗi và 6 cảnh báo hiện hữu trong store.jsx. Vite vẫn cảnh báo bundle lớn hơn 500 kB; chưa tối ưu tải thư viện theo trang.
- B0–B3 đọc CSV/backtest gốc, độc lập kỳ lọc. TARGET lịch sử và rủi ro dự báo có phạm vi khác nhau; không dùng chúng làm bằng chứng nhân quả hay nợ xấu BNPL thực tế.
- Backend AI có thể trả số liệu tham chiếu chưa khớp metadata hiện có; giao diện nhắc đối chiếu trang Đánh giá mô hình. Backend không được sửa.

## Chạy lại tại thư mục aura_handover

```powershell
node --test web/tests/overview.test.mjs web/tests/workflow.test.mjs
npm --prefix web run build
```

Kiểm thử backend DEMO khi môi trường Python đã có đủ phụ thuộc:

```powershell
$env:AURA_DEMO = "1"
python -m pytest -q tests/test_api_demo.py tests/test_evidence_csv.py
```

`BACKEND_SHA256.json` lưu mã băm đối chiếu 35 tệp gốc. Gói ZIP cuối được kiểm tra giải nén và đối chiếu lại toàn bộ 35 tệp này.
