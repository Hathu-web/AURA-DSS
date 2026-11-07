# Yêu cầu chức năng FR-01 đến FR-08
@tags: fr-01, fr-02, fr-03, fr-04, fr-05, fr-06, fr-07, fr-08, yêu cầu chức năng, nghiệp vụ

Danh mục yêu cầu chức năng trong báo cáo Phase 2:
- FR-01 Nhập liệu và lưu trữ: tiếp nhận dữ liệu giao dịch/hồ sơ, lưu star schema, tách PII ra bảng riêng (DIM_CUSTOMER_PII).
- FR-02 Chấm điểm tự động: mô hình LightGBM trả về xác suất FPD cho từng khách, có router Thick/Thin theo độ dày lịch sử tín dụng.
- FR-03 Phân tầng rủi ro: 3 tầng LOW/MEDIUM/HIGH theo ngưỡng cấu hình trong meta.json, không hard-code trong code.
- FR-04 Tối ưu phân bổ vốn: MILP chọn danh mục duyệt sao cho lợi nhuận sau rủi ro lớn nhất trong ràng buộc quỹ và trần nợ xấu.
- FR-05 Ghi nhật ký quyết định: mọi lô duyệt ghi vào FACT_DECISION_LOG kèm batch_id, model_used, phí.
- FR-06 Giải thích quyết định: hiển thị yếu tố tăng/giảm rủi ro (SHAP) bằng ngôn ngữ tiếng Việt định tính, loại bỏ biến nhân khẩu học.
- FR-07 Bảo vệ riêng tư: che PII (họ tên, điện thoại, thiết bị, GPS) trước khi dữ liệu rời hệ thống, có audit log.
- FR-08 Bảng điều khiển và đánh giá: tổng quan KPI, danh mục, thẩm định, tối ưu vốn, đánh giá mô hình, nhật ký.
