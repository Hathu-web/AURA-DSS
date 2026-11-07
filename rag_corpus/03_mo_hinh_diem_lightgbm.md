# Mô hình chấm điểm LightGBM và bộ phân tầng
@tags: lightgbm, auc, thick, thin, router, ngưỡng, tầng, mô hình, brier, ks, gini

Mô hình chấm điểm dùng LightGBM với hai biến thể: Thick-file (khách có lịch sử đầy đủ, 188 đặc trưng) và Thin-file (khách mới, ít lịch sử, 82–86 đặc trưng). Router chọn biến thể theo độ dày lịch sử tín dụng. Số liệu kiểm chứng (run_context: notebook, holdout): AUC Thick 0.7900, AUC Thin 0.7704, Brier 0.06547, Gini 0.58, KS 0.4357, PR-AUC 0.2911; bộ dữ liệu huấn luyện 246.005 dòng, holdout 61.502 dòng (nguồn nhãn: TARGET Home Credit, không phải FPD BNPL thực). Nợ xấu backtest 2,86% ± 0,54 so với nền 8,07%.

Phân tầng: theo meta.json, LOW khi p dưới ngưỡng low_max, MEDIUM khi p dưới medium_max, còn lại HIGH. Phân bố holdout tham chiếu: LOW 52% (bad 2,41%), MEDIUM 22,2% (bad 7,09%), HIGH 25,8% (bad 20,33%). Độ quan trọng nhóm đặc trưng: hồ sơ 44%, lịch sử trước đây 12,9%, bureau 11,7%, trả góp 11,6%, khác 19,8%. Kịch bản Thin-file đạt AUC 0.7704 khi lịch sử bị che.
