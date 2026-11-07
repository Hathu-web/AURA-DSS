# Riêng tư dữ liệu và bảo vệ PII
@tags: pii, riêng tư, nghị định 13, privacy, masking, audit, bảo mật

Hệ thống tuân thủ tinh thần Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân. Biện pháp: (1) PII nằm riêng ở DIM_CUSTOMER_PII, không trộn vào bảng phân tích; (2) PrivacyGuard che họ tên (giữ họ, che tên đệm/tên), che số điện thoại (3 số đầu + **** + 3 số cuối), che device_id, làm mờ toạ độ GPS (Geo-blurred) trước khi hiển thị hoặc gửi ra ngoài; (3) audit log ghi lại mọi lần che với mốc thời gian; (4) câu hỏi người dùng được che email và số điện thoại bằng regex trước khi gửi tới LLM; (5) guardrail kiểm tra số: liệt kê mọi con số trong câu trả lời LLM không có trong FACTS để người dùng đối chiếu. Trợ lý Agent không nạp PII vào ngữ cảnh, kể cả khi hỏi về một khách hàng cụ thể.
