# MILP tối ưu phân bổ vốn (PuLP/CBC)
@tags: milp, pulp, cbc, tối ưu, phân bổ vốn, trần rủi ro, quỹ, lgd, baseline

Bài toán tối ưu dùng lập trình nguyên hỗn hợp (MILP) với solver CBC qua thư viện PuLP. Biến quyết định: duyệt/không duyệt từng đơn trong lô. Hàm mục tiêu: cực đại lợi nhuận kỳ vọng = phí MDR của lô duyệt trừ tổn thất kỳ vọng (số tiền × xác suất FPD × LGD). Ràng buộc: tổng giải ngân ≤ quỹ khả dụng; nợ xấu dự đoán của lô duyệt ≤ trần rủi ro; mỗi đơn tối đa một quyết định. Tham số đầu vào gồm: quỹ vốn (mặc định 2 tỷ), trần rủi ro (mặc định 4%, giới hạn hợp lệ 0,5%–30%), LGD (mặc định 0,6), cỡ lô n (≤2000), seed.

Baseline so sánh (run_context: notebook): B0 duyệt tất cả FIFO có nợ xấu thật 7,63% và lợi nhuận âm; B1 quy tắc thủ công; B2 mô hình + ngưỡng FIFO; B3 AURA (tầng + MILP) giữ nợ xấu thật khoảng 2,3–2,8% đồng thời giữ tỷ lệ duyệt hợp lý. Độ nhạy: giảm trần rủi ro làm tăng khách tốt bị từ chối; tăng quỹ làm giảm biên lợi nhuận trên mỗi tỷ vốn. Kết quả MILP chỉ ghi vào FACT_DECISION_LOG khi người dùng bấm ghi nhật ký.
