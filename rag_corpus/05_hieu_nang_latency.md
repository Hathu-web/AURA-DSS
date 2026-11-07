# Hiệu năng và thời gian phản hồi
@tags: p99, latency, hiệu năng, 102ms, thời gian phản hồi, end-to-end

Chỉ số hiệu năng ghi trong meta.json (run_context: notebook): P99 tính điểm mô hình 102 ms; P99 end-to-end và P99 feature store được ghi trong nhóm latency_ms của metadata. Mục tiêu thiết kế: toàn bộ luồng chấm điểm + giải thích + tối ưu lô 1000 đơn hoàn tất trong vài giây trên máy cá nhân, phù hợp demo hội đồng. Trợ lý Agent khi gọi công cụ phải ghi lại thời gian (ms) của từng bước vào trace để minh bạch hiệu năng tại chỗ chạy thật (LIVE).

Lưu ý so sánh số (run_context): kết quả notebook (ví dụ 534/1000 đơn được duyệt trong một seed cụ thể) có thể khác kết quả LIVE trên dashboard (ví dụ 637/1000) vì lô dữ liệu, seed và tham số khác nhau; khi trả lời cần nêu rõ ngữ cảnh chạy, không trộn số giữa hai ngữ cảnh.
