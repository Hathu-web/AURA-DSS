# AURA-DSS V3 — hướng dẫn trình bày dashboard

Ngày 23/10/2026. Tổng quan và bộ khung được giữ đúng V2 đã duyệt; bảy trang còn lại dùng cùng phong cách trắng, tím và lavender. Backend, dữ liệu và minh chứng gốc giữ nguyên.

## Mạch báo cáo

| Bước | Trang | Câu nói dẫn dắt |
| --- | --- | --- |
| 1 | Tổng quan | “Tôi xác định quy mô danh mục và tín hiệu rủi ro cần xem xét trong kỳ.” |
| 2 | Danh mục | “Tôi khoanh vùng merchant, tầng rủi ro rồi mở hồ sơ liên quan để tìm căn cứ.” |
| Bổ sung | Thẩm định | “Điểm hồ sơ chịu tác động từ những yếu tố này; SHAP giải thích dự báo, chưa chứng minh nguyên nhân.” |
| 3 | Tối ưu vốn | “Với quỹ và trần rủi ro này, hệ thống đề xuất chọn bao nhiêu giao dịch, dùng bao nhiêu vốn và đạt lợi ích kỳ vọng nào?” |
| 4 | Đánh giá mô hình | “Tôi đối chiếu chất lượng mô hình, nguồn backtest B0–B3 và đánh đổi về khách tốt bị từ chối.” |
| 5 | Trợ lý AI | “Tôi dùng câu hỏi cụ thể để giải thích số liệu, đối chiếu bảng bằng chứng và giới hạn của phản hồi.” |

Bấm biểu tượng **Thuyết trình** để ẩn sidebar và hiện mạch 5 bước. Các trang chi tiết cho phép cuộn dọc để dành không gian đọc chữ và bằng chứng; không ép toàn bộ phân tích vào một màn hình.

## Danh mục

- Bốn KPI lấy từ API: số giao dịch, rủi ro trung bình, tỷ trọng HIGH và giá trị giao dịch HIGH. Giá trị HIGH không phải tổn thất.
- Histogram dùng trục xác suất số và ngưỡng từ health API. Nhóm cuối gồm xác suất từ 48% trở lên theo cách gộp của API.
- Dự báo/TARGET theo tầng dùng cột; tỷ lệ chọn dùng trục phải ghi rõ Chọn (%).
- Xếp hạng merchant đổi theo rủi ro, tỷ trọng HIGH hoặc số giao dịch; bấm thanh hoặc ô nhiệt để lọc bảng.
- Tìm mã giao dịch/khách hàng, lọc merchant/tầng, đổi thứ tự và giới hạn số dòng; bấm mã khách để mở Thẩm định.
- Bộ lọc bảng không làm thay đổi biểu đồ tổng hợp. Tối ưu vốn dùng cả lô trong kỳ, không tự nhận bộ lọc merchant của bảng.

## Thẩm định

- Nhận mã khách từ Danh mục hoặc nhập form mới; Thin/Thick do backend chọn.
- Điểm được thể hiện trên thang 0–100%, không cắt về 30% như gauge cũ.
- SHAP có biểu đồ và danh sách đầy đủ tên/yếu tố/chiều tác động. Hạn mức là gợi ý.
- Đổi mã, đổi form hoặc mẫu sẽ xóa kết quả cũ. Thời gian phản hồi là của lần gọi hiện tại, không thay cho P99.
- Form mới chưa tự thêm vào danh mục hoặc lô tối ưu.

## Tối ưu vốn

- Bốn tham số: quỹ, trần rủi ro, LGD, cỡ lô; tùy chọn lấy kỳ đang lọc.
- Giữ nguyên optimize/sensitivity/log API và thuật toán. Ghi đúng tên solver và trạng thái; DEMO là heuristic mô phỏng.
- Kết quả có KPI, phần vốn còn lại, khoảng cách đến trần và TARGET hậu kiểm; không có giao dịch được chọn thì không gán tỷ lệ rủi ro bằng 0.
- What-if có hai biểu đồ với trục được ghi đơn vị. Bấm điểm/cột để điền tham số rồi chạy lại.
- Đổi tham số hoặc kỳ làm kết quả cũ được đánh dấu; khóa ghi nhật ký cho đến khi chạy lại. Sau ghi thành công mở đúng batch, tránh ghi lặp từ cùng nút.
- Xuất CSV đúng dấu nháy, dấu phẩy, xuống dòng và hạn chế chuỗi công thức.

## Đánh giá và Trợ lý AI

- AUC Thin-file thiếu vẫn ghi Chưa xác minh. Các số ablation/importance/holdout tham chiếu nằm trong phần thu gọn với nhãn nguồn rõ ràng.
- B0–B3 đọc dữ liệu của cùng mức quỹ; nêu cả lợi ích, TARGET và khách tốt bị từ chối. Không chỉ trình bày mặt thuận lợi.
- Fairness theo nhóm có bảng đối chiếu dự báo, TARGET, độ lệch và số hồ sơ; chênh lệch mô tả chưa đủ kết luận công bằng.
- Trợ lý AI dùng giao diện sáng; câu hỏi, phản hồi, bảng dữ liệu, SQL và cảnh báo có khu vực rõ ràng.
- Mỗi phản hồi giữ kỳ dữ liệu lúc gửi. Bảng gần nhất ghi đúng câu hỏi sinh ra bảng, kể cả sau câu hỏi mới không có bảng.
- Mã khách hàng giữ nguyên chữ số, không định dạng thành số tiền. Phản hồi ngoại tuyến được ghi đúng trạng thái; lỗi có nút thử lại.
- Nếu AI nêu AUC Thin-file, đối chiếu Đánh giá mô hình; backend hỏi đáp gốc có số tham chiếu tĩnh và chưa được thay đổi.

## Nhập dữ liệu và Nhật ký

- Nhận CSV/XLSX, tối đa 5 MB/500 dòng; không nhận XLS. Đổi loại tệp xóa kết quả cũ; có thể chọn lại cùng tệp.
- Hiển thị số dòng chấm được, dòng lỗi, cột thiếu và kết quả; dòng dữ liệu bắt đầu từ 1 không tính tiêu đề.
- Upload hồ sơ là phân tích tệp, không khẳng định đã lưu hồ sơ vào database. Lô giao dịch cần CUSTOMER_SCORE thật, DEMO trả giới hạn rõ ràng.
- Nhật ký có chọn batch, giới hạn dòng, làm mới, CSV và đối chiếu tổng hợp. Số liệu chỉ nói về phạm vi đã tải, không tự coi là toàn bộ lịch sử.
- Phí trong nhật ký là phí theo đề xuất, chưa phải doanh thu thu được. Audit chỉ hiển thị thời điểm/tên trường/số lượng được API trả về.

## Chỉnh chữ và chạy lại

Xem **HUONG_DAN_SUA_CO_CHU.md**: vị trí selector Tổng quan, CSS tùy chọn giúp thẻ tự giãn, các biến font trang mới và lệnh build.

Xem **NGHIEM_THU_UI.md** để biết phạm vi đã kiểm thử và các giới hạn DEMO/LIVE.
