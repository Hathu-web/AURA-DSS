# Tổng quan hệ thống AURA-DSS
@tags: tổng quan, kiến trúc, mục tiêu, bnpl, hệ hỗ trợ ra quyết định, phase 2

AURA-DSS là hệ hỗ trợ ra quyết định tín dụng BNPL (mua trước trả sau) gồm ba lớp: (1) lớp dữ liệustar schema SQLite với FACT_BNPL_TRANSACTION, FACT_DECISION_LOG, CUSTOMER_SCORE, DIM_CUSTOMER, DIM_CUSTOMER_PII, FEATURE_STORE; (2) lớp phân tích gồm mô hình LightGBM chấm điểm xác suất FPD (first payment default), bộ phân tầng rủi ro 3 tầng LOW/MEDIUM/HIGH và bài toán MILP tối ưu phân bổ vốn (PuLP/CBC); (3) lớp ứng dụng gồm dashboard React và API FastAPI. Mục tiêu kinh doanh: tăng lợi nhuận sau rủi ro và giảm nợ xấu so với baseline duyệt tất cả (B0) và quy tắc thủ công (B1).

Phạm vi của nguyên tắc Agentic: trợ lý AI chỉ DIỄN GIẢI số liệu từ ngữ cảnh FACTS do công cụ trả về, tuyệt đối không tự sinh số liệu nghiệp vụ, không tự thay tầng rủi ro, xác suất hay quyết định đã có. Mọi hành động ghi dữ liệu phải đi qua cổng xác nhận.
