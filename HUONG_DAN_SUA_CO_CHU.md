# Chỗ sửa cỡ chữ AURA-DSS V3

Tổng quan được giữ đúng bản V2 đã duyệt. Bảy trang còn lại đã được thiết kế lại theo cùng phong cách trắng/tím/lavender với chữ và khoảng cách lớn hơn. Backend giữ nguyên.

## Tổng quan

Mở thư mục `aura_handover` trong VS Code. Ctrl+P tìm `web/src/reference.css`, Ctrl+F tìm selector:

| Phần muốn sửa | Selector |
| --- | --- |
| Nội dung Insight | `.priority-copy p` |
| Tiêu đề từng Insight | `.priority-copy h4` |
| Tiêu đề thẻ biểu đồ | `.executive-card-header h3` |
| Bảng merchant | `.merchant-table`, `.merchant-table th` |
| Số KPI | `.stat-value` |
| Nhãn KPI | `.stat-label` |

Cuối file có các khối `@media` ghi đè cỡ chữ. Dán CSS tùy chỉnh **ở cuối file, sau toàn bộ `@media`**, để tránh sửa đầu file nhưng chữ vẫn nhỏ.

Cách nhanh: sao chép toàn bộ nội dung **`web/customize/overview-readable.css`**, dán vào cuối **`web/src/reference.css`**. File tùy chọn chưa được nạp tự động.

Mức khởi đầu: Insight 12px, tiêu đề Insight 13px, tiêu đề thẻ 14px, bảng 12px. Có thể thử tăng thêm 1–2px khi trình chiếu, rồi kiểm tra trên máy chiếu thực tế.

Đoạn CSS đi kèm `height: auto`, giãn dòng và khoảng cách để thẻ tự giãn. Trang có thể cần cuộn dọc; không ép chữ lớn vào thẻ cố định chiều cao. Bảng rộng cuộn ngang trong khung riêng.

## Chữ trong biểu đồ

Mở **`web/src/pages/Overview.jsx`**, tìm `fontSize`. Nhãn trục, nhãn giá trị và chú giải nằm trong cấu hình ECharts, không được đổi chỉ bằng CSS ngoài.

Có thể thử tăng các `fontSize: 9` hoặc `fontSize: 10` thành 11–12. Kiểm tra lại ba biểu đồ ở chiều rộng màn hình đang dùng. Không sửa tên trường API hoặc công thức khi chỉ chỉnh chữ.

## Các trang còn lại

Mở **`web/src/pages.css`**, sửa ba biến đầu file:

```css
:root {
  --page-body-size: 14px;
  --page-title-size: 16px;
  --page-note-size: 12px;
}
```

Có thể thử `15px / 18px / 13px`. Những phần có cỡ riêng như số KPI, nút nhỏ và nhãn trạng thái có selector riêng trong cùng file. Cỡ chữ biểu đồ dùng chung ở **`web/src/lib/chartTheme.js`** (`flowAxis.axisLabel.fontSize`, `flowLegend.textStyle.fontSize`); nhãn từng cột/điểm ở `fontSize` trong từng file trang.

| Trang | File cần sửa |
| --- | --- |
| Tổng quan | `web/src/pages/Overview.jsx` |
| Danh mục | `web/src/pages/Portfolio.jsx` |
| Thẩm định | `web/src/pages/Appraisal.jsx` |
| Tối ưu vốn | `web/src/pages/Optimize.jsx` |
| Đánh giá mô hình | `web/src/pages/Evaluation.jsx` |
| Trợ lý AI | `web/src/pages/Assistant.jsx` |
| Nhập dữ liệu | `web/src/pages/Ingest.jsx` |
| Nhật ký | `web/src/pages/Logs.jsx` |

Trong trang mới, tìm `StoryIntro` để sửa câu dẫn đầu, `FlowCard` cho tiêu đề khối, `EvidenceNote` cho nhận định/chú thích, `NextAction` cho câu chuyển trang. Component chung ở **`web/src/components/workflow.jsx`**. Giữ số liệu động lấy từ API.

Bấm biểu tượng **Thuyết trình** trên thanh đầu trang để ẩn sidebar và hiện mạch báo cáo; các trang mới cũng có mức chữ lớn hơn ở chế độ này.

## Build sau khi chỉnh

Mở PowerShell tại **`aura_handover`** — thư mục có `api.py` và `web`.

Lần đầu nếu chưa cài thư viện frontend:

```powershell
npm --prefix web ci
```

Sau mỗi lần sửa JSX/CSS:

```powershell
npm --prefix web run build
```

Lệnh tạo lại `web_build`, là thư mục backend đang phục vụ. Quay lại trình duyệt bấm **Ctrl+F5**. Chỉ sửa `web/src` rồi refresh sẽ chưa thay đổi bản build đang chạy.

Để cập nhật dự án đang chạy: sao lưu frontend cũ rồi chép **`web` và `web_build`** từ gói V3 vào thư mục dự án hiện tại. Giữ môi trường Python, database, model và cấu hình backend đang dùng. Gói đã kèm `web_build` để xem ngay; cần Node.js/npm khi tự chỉnh và build frontend.
