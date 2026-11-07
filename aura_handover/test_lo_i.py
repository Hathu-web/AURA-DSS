# =====================================================================================
#  KIỂM THỬ LÕI TRƯỚC KHI BÀN GIAO UI – chạy trên Colab (đã mount Drive, pip install pulp shap lightgbm)
#  Cách chạy:  %cd "/content/drive/MyDrive/Colab Notebooks/aura_handover"   rồi   %run test_lo_i.py
#  Yêu cầu thư mục aura_handover có features.py, model.py, llm.py; cạnh nó là fpd_model_v1/, fpd_model_thin/, aura_bnpl.db
# =====================================================================================
import time, json, numpy as np, pandas as pd
from model import FPDModel

BASE = "/content/drive/MyDrive/Colab Notebooks/"
m = FPDModel(model_dir=BASE + "fpd_model_v1", db_path=BASE + "aura_bnpl.db")
print("1. Nạp mô hình:", len(m.boosters), "booster thick |", len(m.boosters_thin or []), "booster thin |",
      len(m.feats), "/", len(m.feats_thin or []), "đặc trưng")
assert m.boosters_thin, "Không tìm thấy fpd_model_thin cạnh fpd_model_v1"

# 2. Chấm khách có sẵn (tra bảng) và chấm lại (tính) – phải khớp
r1 = m.score_customer(243023); print("2a. score_customer (tra bảng):", r1)
with m._conn() as c:
    c.execute("CREATE TEMP TABLE _bk AS SELECT * FROM CUSTOMER_SCORE WHERE customer_id=243023")
d = pd.read_sql("SELECT * FROM DIM_CUSTOMER WHERE customer_id=243023", m._conn()).rename(columns={"customer_id": "SK_ID_CURR"})
X = m._features_from_raw(d); p_calc = float(m._predict(X, m.route(X))[0])
print(f"2b. tính lại: p={p_calc:.6f} | router={m.route(X)} | lệch so với bảng {abs(p_calc - r1['p']):.2e}")
assert abs(p_calc - r1["p"]) < 1e-4

# 3. Khách mới nhập form (chỉ hồ sơ) -> phải đi luồng thin
form = {"NAME_CONTRACT_TYPE": "Cash loans", "AMT_INCOME_TOTAL": 180000, "AMT_CREDIT": 450000, "AMT_ANNUITY": 25000,
        "AMT_GOODS_PRICE": 400000, "DAYS_BIRTH": -12000, "DAYS_EMPLOYED": -1500, "EXT_SOURCE_2": 0.55, "EXT_SOURCE_3": 0.45,
        "NAME_EDUCATION_TYPE": "Higher education", "NAME_FAMILY_STATUS": "Married", "NAME_HOUSING_TYPE": "House / apartment",
        "OCCUPATION_TYPE": "Core staff", "ORGANIZATION_TYPE": "Business Entity Type 3", "REGION_RATING_CLIENT": 2,
        "CNT_CHILDREN": 1, "CNT_FAM_MEMBERS": 3, "FLAG_OWN_CAR": "N", "FLAG_OWN_REALTY": "Y"}
t = time.perf_counter(); r3 = m.score_new(form); dt = (time.perf_counter() - t) * 1000
print(f"3. score_new: {r3} | {dt:.1f} ms"); assert r3["model_used"] == "thin"

# 4. Giải thích SHAP cho cả hai luồng
e1 = m.explain(243023); print("4a. explain thick:", e1["model_used"], [x["ten"] for x in e1["tang_rui_ro"]])
e2 = m.explain(form=form); print("4b. explain thin :", e2["model_used"], [x["ten"] for x in e2["tang_rui_ro"]])

# 5. MILP – phải ra đúng 660 đơn / 43,04 triệu như notebook
d_lo, kq = m.optimize(liquidity=2e9, risk_ceiling=0.04, lgd=0.6, n=1000, seed=42)
print(f"5. MILP {kq['solver']} {kq['status']} {kq['solve_s']:.3f}s | duyệt {kq['so_don_duyet']} | LN kỳ vọng {kq['loi_nhuan_kv']/1e6:.2f} tr "
      f"| nợ xấu dự đoán {kq['no_xau_du_doan']*100:.2f}% | theo model {kq['theo_model']}")
assert kq["status"] == "Optimal" and kq["so_don_duyet"] == 660, "Kết quả MILP lệch notebook – kiểm tra lại lô/seed"
print("   lý do từ chối:", d_lo[d_lo.decision == 0]["ly_do"].value_counts().to_dict())

# 6. Độ nhạy + ghi log
sens = m.sensitivity(); print("6a. sensitivity:\n", sens.round(4).to_string(index=False))
bid = m.log_decisions(d_lo, batch_id="BATCH_TEST_UI"); print("6b. đã ghi log batch", bid)
print("7. portfolio_summary keys:", list(m.portfolio_summary().keys()))
print("\n✅ LÕI SẴN SÀNG BÀN GIAO")
