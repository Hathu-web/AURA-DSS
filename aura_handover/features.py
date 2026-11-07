"""
features.py – Dựng đặc trưng cho mô hình FPD v1 (TÁCH TỪ NOTEBOOK, KHÔNG SỬA LOGIC)
Dùng chung cho: huấn luyện, feature store, dashboard, API.

Hai hàm chính:
    tao_dac_trung(d, cat_categories)   -> đặc trưng từ hồ sơ (DIM_CUSTOMER / application)
    ghep_lich_su(X, d, aux)            -> ghép thêm đặc trưng lịch sử (aux_features.parquet)
"""
import numpy as np
import pandas as pd

CAT_COLS = ["NAME_CONTRACT_TYPE", "FLAG_OWN_CAR", "FLAG_OWN_REALTY", "NAME_INCOME_TYPE", "NAME_EDUCATION_TYPE",
            "NAME_FAMILY_STATUS", "NAME_HOUSING_TYPE", "OCCUPATION_TYPE", "ORGANIZATION_TYPE",
            "NAME_TYPE_SUITE", "WEEKDAY_APPR_PROCESS_START"]
NUM_COLS = ["AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "AMT_GOODS_PRICE", "DAYS_BIRTH", "DAYS_EMPLOYED",
            "DAYS_REGISTRATION", "DAYS_ID_PUBLISH", "DAYS_LAST_PHONE_CHANGE", "CNT_CHILDREN", "CNT_FAM_MEMBERS",
            "REGION_POPULATION_RELATIVE", "REGION_RATING_CLIENT", "REGION_RATING_CLIENT_W_CITY", "OWN_CAR_AGE",
            "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3",
            "OBS_30_CNT_SOCIAL_CIRCLE", "DEF_30_CNT_SOCIAL_CIRCLE", "OBS_60_CNT_SOCIAL_CIRCLE", "DEF_60_CNT_SOCIAL_CIRCLE",
            "AMT_REQ_CREDIT_BUREAU_HOUR", "AMT_REQ_CREDIT_BUREAU_DAY", "AMT_REQ_CREDIT_BUREAU_WEEK",
            "AMT_REQ_CREDIT_BUREAU_MON", "AMT_REQ_CREDIT_BUREAU_QRT", "AMT_REQ_CREDIT_BUREAU_YEAR",
            "HOUR_APPR_PROCESS_START", "DAYS_EMPLOYED_ANOM",
            "FLAG_MOBIL", "FLAG_EMP_PHONE", "FLAG_WORK_PHONE", "FLAG_CONT_MOBILE", "FLAG_PHONE", "FLAG_EMAIL",
            "REG_REGION_NOT_LIVE_REGION", "REG_REGION_NOT_WORK_REGION", "LIVE_REGION_NOT_WORK_REGION",
            "REG_CITY_NOT_LIVE_CITY", "REG_CITY_NOT_WORK_CITY", "LIVE_CITY_NOT_WORK_CITY"]
DOC_COLS = [f"FLAG_DOCUMENT_{i}" for i in range(2, 22)]
CONTACT_COLS = ["FLAG_MOBIL", "FLAG_EMP_PHONE", "FLAG_WORK_PHONE", "FLAG_CONT_MOBILE", "FLAG_PHONE", "FLAG_EMAIL"]
REGION_COLS = ["REG_REGION_NOT_LIVE_REGION", "REG_REGION_NOT_WORK_REGION", "LIVE_REGION_NOT_WORK_REGION",
               "REG_CITY_NOT_LIVE_CITY", "REG_CITY_NOT_WORK_CITY", "LIVE_CITY_NOT_WORK_CITY"]


def ep_kieu_so(d: pd.DataFrame) -> pd.DataFrame:
    """SQLite trả None cho NULL -> phải ép về float NaN trước khi tính toán (bắt buộc khi đọc 1 dòng)."""
    d = d.copy()
    cols = [c for c in NUM_COLS + DOC_COLS if c in d.columns]
    d[cols] = d[cols].apply(pd.to_numeric, errors="coerce")
    return d


def tao_dac_trung(d: pd.DataFrame, cat_categories: dict | None = None) -> pd.DataFrame:
    """d: DataFrame có các cột gốc Home Credit (hoặc DIM_CUSTOMER đã đổi customer_id -> SK_ID_CURR)."""
    d = ep_kieu_so(d)
    if "DAYS_EMPLOYED_ANOM" not in d:
        d["DAYS_EMPLOYED_ANOM"] = (d["DAYS_EMPLOYED"] == 365243).astype(int)
        d["DAYS_EMPLOYED"] = d["DAYS_EMPLOYED"].replace(365243, np.nan)
    X = d.reindex(columns=NUM_COLS + CAT_COLS)
    inc, cre, ann, gp = d["AMT_INCOME_TOTAL"], d["AMT_CREDIT"], d["AMT_ANNUITY"], d["AMT_GOODS_PRICE"]
    fam = d["CNT_FAM_MEMBERS"].replace(0, np.nan)
    age_y = -d["DAYS_BIRTH"] / 365
    X["credit_income_ratio"] = cre / inc
    X["annuity_income_ratio"] = ann / inc
    X["credit_term"] = cre / ann
    X["credit_goods_ratio"] = cre / gp
    X["goods_income_ratio"] = gp / inc
    X["credit_minus_goods"] = cre - gp
    X["income_per_person"] = inc / fam
    X["income_per_child"] = inc / (1 + d["CNT_CHILDREN"])
    X["annuity_per_person"] = ann / fam
    X["children_ratio"] = d["CNT_CHILDREN"] / fam
    X["age_years"] = age_y
    X["employed_years"] = -d["DAYS_EMPLOYED"] / 365
    X["employed_age_ratio"] = d["DAYS_EMPLOYED"] / d["DAYS_BIRTH"]
    X["phone_change_ratio"] = d["DAYS_LAST_PHONE_CHANGE"] / d["DAYS_BIRTH"]
    X["id_publish_ratio"] = d["DAYS_ID_PUBLISH"] / d["DAYS_BIRTH"]
    X["registration_ratio"] = d["DAYS_REGISTRATION"] / d["DAYS_BIRTH"]
    X["credit_term_vs_age"] = (cre / ann) / age_y
    ext = d[["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]]
    X["ext_mean"] = ext.mean(axis=1); X["ext_min"] = ext.min(axis=1); X["ext_max"] = ext.max(axis=1)
    X["ext_std"] = ext.std(axis=1); X["ext_prod"] = ext.prod(axis=1, min_count=1)
    X["ext_nan_cnt"] = ext.isna().sum(axis=1)
    X["ext_w"] = d["EXT_SOURCE_1"] * 2 + d["EXT_SOURCE_2"] * 3 + d["EXT_SOURCE_3"] * 4
    X["ext1_x_age"] = d["EXT_SOURCE_1"] * age_y
    X["ext2_x_employed"] = d["EXT_SOURCE_2"] * X["employed_years"]
    X["ext_mean_x_annuity_ratio"] = X["ext_mean"] * X["annuity_income_ratio"]
    X["def_obs_30_ratio"] = d["DEF_30_CNT_SOCIAL_CIRCLE"] / (1 + d["OBS_30_CNT_SOCIAL_CIRCLE"])
    X["bureau_req_total"] = d.reindex(columns=[c for c in NUM_COLS if c.startswith("AMT_REQ_")]).sum(axis=1, min_count=1)
    docs = d.reindex(columns=DOC_COLS)
    X["doc_count"] = docs.sum(axis=1, min_count=1)
    X["flag_doc_3"] = docs["FLAG_DOCUMENT_3"] if "FLAG_DOCUMENT_3" in docs else np.nan
    X["contact_count"] = d.reindex(columns=CONTACT_COLS).sum(axis=1, min_count=1)
    X["region_mismatch_cnt"] = d.reindex(columns=REGION_COLS).sum(axis=1, min_count=1)
    X = X.replace([np.inf, -np.inf], np.nan)
    for c in CAT_COLS:
        cats = cat_categories[c] if cat_categories else sorted(X[c].dropna().unique())
        X[c] = pd.Categorical(X[c], categories=cats)
    return X


def ghep_lich_su(X: pd.DataFrame, d: pd.DataFrame, aux: pd.DataFrame) -> pd.DataFrame:
    """X: output tao_dac_trung | d: DataFrame gốc có SK_ID_CURR | aux: aux_features.parquet (index SK_ID_CURR)."""
    d = ep_kieu_so(d)
    X = X.join(aux.reindex(d["SK_ID_CURR"].values).set_index(X.index))
    X["has_bureau"] = X["bu_cnt"].notna().astype(int)
    X["has_prev"] = X["pv_cnt"].notna().astype(int)
    inc = d["AMT_INCOME_TOTAL"].values
    X["bu_debt_income_ratio"] = X["bu_debt_sum"] / inc
    X["total_annuity_income"] = (d["AMT_ANNUITY"].values + X["bu_annuity_sum"].fillna(0)) / inc
    X["credit_vs_prev_max"] = d["AMT_CREDIT"].values / X["pv_amt_credit_max"]
    X["credit_vs_bu_max"] = d["AMT_CREDIT"].values / X["bu_credit_max"]
    X["ext_mean_x_ontime"] = X["ext_mean"] * (1 - X["ins_late_rate"].fillna(0))
    X["pay_ratio_x_ext"] = X["ins_pay_ratio_mean"] * X["ext_mean"]
    return X.replace([np.inf, -np.inf], np.nan)
