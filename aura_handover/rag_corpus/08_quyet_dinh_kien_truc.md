# Quyết định kiến trúc chính
@tags: kiến trúc, quyết định, star schema, fastapi, react, sqlite, thiết kế, database

Các quyết định kiến trúc được ghi nhận trong báo cáo: (1) dùng SQLite star schema thay vì CSDL máy chủ vì phạm vi đồ án và dễ đóng gói; (2) tách bảng PII riêng để thu hẹp bề mặt rò rỉ; (3) FastAPI bọc lõi model.py/llm.py, vừa phục vụ JSON vừa phục vụ web build tĩnh; (4) React SPA với các trang: Tổng quan, Danh mục, Thẩm định, Tối ưu vốn, Đánh giá, Trợ lý, Nhập dữ liệu, Nhật ký; (5) LLM (Gemini) chỉ ở tầng diễn giải, có chuỗi model dự phòng và cơ chế degradation về mẫu ngoại tuyến; (6) mọi tham số chính sách (ngưỡng tầng, hạn mức) đọc từ meta.json; (7) MILP dùng PuLP/CBC với time limit 30 giây; (8) token truy cập API tuỳ chọn qua header X-Aura-Token khi chia sẻ công khai.
