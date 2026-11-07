# Bằng chứng và phạm vi số liệu cho Chương 6–7

Bổ sung ngày 14/10/2026 từ 4 tệp người dùng cung cấp:

- `baseline_comparison.csv`: 40 lượt mô phỏng, hai mức quỹ 1,5 và 2,0 tỷ VNĐ, 20 seed mỗi mức. So sánh 4 phương án B0–B3. Dữ liệu phản ánh hiệu quả **mô phỏng và hậu kiểm bằng nhãn Home Credit**, không phải dòng tiền BNPL thật.
- `fairness.csv`: 19 nhóm, chia theo 5 tiêu chí tuổi, học vấn, hôn nhân, khu vực, giới tính. Số quan sát cho mỗi tiêu chí khác nhau. **Giới tính: chỉ 977 hồ sơ**, không được suy rộng lên 30.000. Học vấn có 29.974; nhóm tuổi, hôn nhân, khu vực có 30.000.
- `evaluation_artifacts/meta_v1.json`: `v1` 188 features, 5 folds, Thick AUC=0.79002354, PR-AUC=0.29114366, Brier=0.06547429, Router Holdout AUC=0.78976954; model_p99=102.0049ms; end_to_end_p99=587.7869ms. P99 mô hình **không đạt mục tiêu dưới 50ms**.
- `evaluation_artifacts/meta_thin_v2.json`: `thin_application_only_v2` 86 features, 5 folds; **không có AUC**, cần cung cấp output notebook để chốt riêng AUC Thin.

## Các quy ước báo cáo và Dashboard

- Phân biệt TARGET Home Credit là nhãn khó khăn thanh toán theo nguồn, **không phải FPD quan sát từ BNPL thực**.
- `baseline_comparison.csv` có nhãn `no_xau_that_gia_tri` và `loi_nhuan_that_trieu`: diễn giải lần lượt như tỷ lệ gắn TARGET **hậu kiểm theo giá trị vốn** và **lợi ích ròng mô phỏng theo kịch bản**, không xem là nợ xấu hay lợi nhuận kinh doanh thực tế.
- Biến `tu_choi_oan` có tên kỹ thuật từ notebook; để diễn giải theo chuẩn Fairness (FPR/FNR, Equal Opportunity...), cần xem công thức và mẫu số trong notebook.
- Biểu đồ ablation (Thick che lịch sử/Thin) và importance groups trong UI hiện là dữ liệu tham chiếu của bản code cũ, chưa được xác thực bằng 4 tệp lần này.
- Các JSON metadata chỉ đủ kiểm chứng thông số, **không đủ chạy mô hình**. Muốn nghiệm thu bộ suy luận và solver cần database, các file `fold_*.txt`, `aux_features.parquet` và CBC/PuLP.

## KPI baseline trung bình theo 20 seed

| Quỹ (tỷ) | Phương án | Lợi ích ròng/lô (triệu) | Rủi ro TARGET theo vốn | Tỷ lệ sử dụng vốn | Khách tốt bị từ chối |
|---|---|---:|---:|---:|---:|
| 2,0 | B0 FIFO | -9,79 | 7,63% | 100% | 28,74% |
| 2,0 | B1 thủ công | 29,54 | 3,98% | 86,52% | 43,11% |
| 2,0 | B2 ML + FIFO | 40,25 | 3,45% | 99,99% | 25,87% |
| 2,0 | B3 Aura MILP | 42,48 | 2,79% | 86,19% | 34,05% |
| 1,5 | B0 FIFO | -7,32 | 7,63% | 100% | 46,53% |
| 1,5 | B1 thủ công | 25,18 | 4,02% | 100% | 50,67% |
| 1,5 | B2 ML + FIFO | 28,68 | 3,63% | 100% | 44,64% |
| 1,5 | B3 Aura MILP | 41,51 | 2,35% | 100% | 43,37% |

Các giá trị được tính từ CSV theo trung bình số học, làm tròn để trình bày. Không thay thế kiểm tra công thức trong notebook.
